import queue
import os
import threading
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from call_management_service import CallManager
from hearing.vad import VADDetect
from hearing.whisper_transcribe import preprocess_transcribe_audio
from hearing.speech_detector import SpeechDetector
from hearing.transcription import TranscriptionService
from language.openai_client import OpenAILLMClient
from speech.tts import text_to_speech_input_streaming

from utils.async_ops import producer


app = FastAPI()

call_manager = CallManager()

class CreateCallRequest(BaseModel):
    voiceId: str

@app.post("/call")
async def create_call(request_body: CreateCallRequest = None):
    print(f"VoiceId: {request_body.voiceId}")
    response = call_manager.create_call(callProperties={
        'voiceId': request_body.voiceId
    })

    return {"message": "Call created", "callObject": response}


@app.websocket("/audio-websocket/ws/audio/{callId}")
async def websocket_audio_endpoint(websocket: WebSocket, callId: str):
    print(f"callId: {callId}")

    call_properties = call_manager.get_call_properties(callId)
    if call_properties is None:
        await websocket.close(code=4001, reason="Call not found")
        return  # Make sure to return after closing to prevent further execution

    await websocket.accept()


    audio_queue = queue.Queue()

    vad_buffer = bytearray()
    transcription_buffer = bytearray()
    audio_padding_size = 640 * 1 # ~ 30ms audio data?


    transcription_service = TranscriptionService()

    def transcript(transcription_buffer):
        print(f"trascript called! with buffer size {len(transcription_buffer)}")
        transcribe_thread = threading.Thread(target=preprocess_transcribe_audio, kwargs={'data': bytes(transcription_buffer), 'transcription_callback': transcription_service.transcription_callback})
        transcription_buffer.clear()
        transcribe_thread.start()

    def complete_transcript():
        full_transcription = transcription_service.get_transcription_and_clear()
        print(f"Querying LLM with transcript {full_transcription}")

        async def handle_async_stuff():
            request = {}
            request['transcript'] = call_manager.add_utterance_to_call(callId, full_transcription, 'user')
            request['interaction_type'] = 'user_message'
            request['response_id'] = 'test123'

            queue1 = asyncio.Queue()
            queue2 = asyncio.Queue()

            llm_client = OpenAILLMClient()
            ag = llm_client.draft_response(request)

            async def consumer(queue):
                agent_response = ''
                while True:
                    item = await queue.get()
                    if item is None:
                        break  # End of stream
                    agent_response += item['content']
                call_manager.add_utterance_to_call(callId, agent_response, 'agent')

               # Start the producer and consumers
            await asyncio.gather(
                producer(ag, [queue1, queue2]),
                text_to_speech_input_streaming(voice_id='KQI7mgK11OmJF02kVxnK', queue=queue1, out_websocket=websocket),               
                consumer(queue2),
            )

        if len(full_transcription.strip()) > 0:
            asyncio.run(handle_async_stuff())

    detector = SpeechDetector(transcription_callback=transcript, complete_callback=complete_transcript, max_audio_padding=audio_padding_size*180)

    vad_thread = threading.Thread(target=VADDetect, kwargs={'audio_buffer': audio_queue, 'callback': detector.silero_response})
    vad_thread.start()

    try:
        while True:
            data = await websocket.receive_bytes()
            
            transcription_buffer.extend(data)
            vad_buffer.extend(data)
            detector.on_audio(data)

            while(len(vad_buffer) >= audio_padding_size):
                frame = vad_buffer[:audio_padding_size]
                audio_queue.put(frame)
                vad_buffer = vad_buffer[audio_padding_size:]

    except WebSocketDisconnect:
        print(f"Websocket closed by client")
        print(f"Call history: {call_manager.get_utterances_for_call(callId)}")
    except Exception as e:
        print(f"socket Error: {e}")
        await websocket.close()
        


if __name__ == "__main__":
    import uvicorn
    MODE = os.environ.get("MODE", "production")
    uvicorn.run("main:app", host="0.0.0.0", port=os.environ.get('PORT', 8000), reload=(MODE == 'development'))