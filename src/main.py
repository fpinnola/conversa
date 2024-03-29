import os
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from call_management_service import CallManager
from hearing.vad import vad_detect
from hearing.speech_detector import SpeechDetector
from language.openai_client import OpenAILLMClient
from speech.tts import text_to_speech_input_streaming
from speech.voice_library import get_elevenlabs_voices

from utils.async_ops import producer


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


call_manager = CallManager()

class CreateCallRequest(BaseModel):
    voiceId: str

@app.get('/voices')
async def get_available_voices():
    response = get_elevenlabs_voices()
    return {"voices": response}

@app.post("/call")
async def create_call(request_body: CreateCallRequest = None):
    print(f"VoiceId: {request_body.voiceId}")
    response = call_manager.create_call(callProperties={
        'voiceId': request_body.voiceId
    })

    return {"message": "Call created", "callObject": response}

@app.websocket("/audio-ws/{callId}")
async def websocket_audio_endpoint(websocket: WebSocket, callId: str):
    print(f"callId: {callId}")
    await websocket.accept()

    call_properties = call_manager.get_call_properties(callId)
    if call_properties is None:
        await websocket.close(code=4001, reason="Call not found")
        return  # Make sure to return after closing to prevent further execution

    audio_queue = asyncio.Queue()

    transcription_buffer = bytearray()
    audio_padding_size = 512 * 1 # ~ 30ms audio data?

    async def agent_text_consumer(queue):
        agent_response = ''
        while True:
            item = await queue.get()
            if item is None:
                break  # End of stream
            agent_response += item['content']
        call_manager.add_utterance_to_call(callId, agent_response, 'agent')

    def complete_transcript():
        full_transcription = detector.get_transcription_and_clear()
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


            await asyncio.gather(
                producer(ag, [queue1, queue2]),
                text_to_speech_input_streaming(voice_id='KQI7mgK11OmJF02kVxnK', queue=queue1, out_websocket=websocket),               
                agent_text_consumer(queue2),
            )

        if len(full_transcription.strip()) > 0:
            asyncio.run(handle_async_stuff())

    async def begin_call():
            llm_client = OpenAILLMClient()

            message = llm_client.draft_begin_message()

            message_queue = asyncio.Queue()

            async def temp_ag():
                await message_queue.put(message)
            
                await message_queue.put({
                    "response_id": 0,
                    "content": "",
                    "content_complete": True,
                    "end_call": False,
                })


            await asyncio.gather(
                temp_ag(),
                text_to_speech_input_streaming(voice_id='KQI7mgK11OmJF02kVxnK', queue=message_queue, out_websocket=websocket, autoflush=True), 
            )


    begin_task = asyncio.create_task(begin_call())


    detector = SpeechDetector(complete_callback=complete_transcript, max_audio_padding=audio_padding_size*180)

    task = asyncio.create_task(vad_detect(audio_queue=audio_queue, callback=detector.silero_response))

    try:
        while True:
            data = await websocket.receive_bytes()
            
            transcription_buffer.extend(data)
            await audio_queue.put(data)
            detector.on_audio(data)

    except WebSocketDisconnect:
        print(f"Websocket closed by client")
        print(f"Call history: {call_manager.get_utterances_for_call(callId)}")
    except Exception as e:
        print(f"socket Error: {e}")
        await websocket.close()
    finally:
        begin_task.cancel()
        task.cancel()
        


if __name__ == "__main__":
    import uvicorn
    MODE = os.environ.get("MODE", "production")
    uvicorn.run("main:app", host="0.0.0.0", port=os.environ.get('PORT', 8000), reload=(MODE == 'development'))