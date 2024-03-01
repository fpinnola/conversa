import queue
import threading
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

load_dotenv()

from vad import VADDetect
from whisper_transcribe import preprocess_transcribe_audio
from call_management_service import CallManager
from llm import LlmClient
from tts import text_to_speech_input_streaming


app = FastAPI()

audio_queue = queue.Queue()

class SpeechDetector:
    def __init__(self, transcription_callback, complete_callback=None):
        self.last_speech_timer = None
        self.llm_timer = None
        self.transcription_delay = 0.5
        self.llm_delay = 3
        self.is_speaking = False
        self.is_paused = True
        self.last_speech = 0
        self.current_transcription = ''
        self.transcription_callback = transcription_callback
        self.complete_callback = complete_callback

    def reset_timers(self):
        if self.last_speech_timer is not None:
            self.last_speech_timer.cancel()
        if self.llm_timer is not None:
            self.llm_timer.cancel()
        
        self.last_speech_timer = threading.Timer(self.transcription_delay, self.transcription_callback)
        self.llm_timer = threading.Timer(self.llm_delay, self.call_llm)

        self.last_speech_timer.start()
        self.llm_timer.start()

    def trigger_transcription(self):
        self.is_paused = True
    
    def call_llm(self):
        self.is_speaking = False
        if self.complete_callback:
            self.complete_callback()

    def silero_response(self, res):
        # print(res)
        if res == "Speech":
            if not self.is_speaking:
                self.is_paused = False
                self.is_speaking = True
            self.reset_timers()


class TranscriptionService:
    def __init__(self):
        self.current_transcription = ""
        pass

    def transcription_callback(self, res):
        self.current_transcription += res

    def get_transcription_and_clear(self):
        res = self.current_transcription
        self.current_transcription = ""
        return res
    
# Add items from Async Generator into a list of queues to be consumed by multiple consumers
async def producer(ag, queues):
    async for item in ag:
        # print(f"producer got item {item}")
        for q in queues:
            await q.put(item)
    for q in queues:
        await q.put(None)  # Signal the consumers that the stream has ended


call_manager = CallManager()
llm_client = LlmClient()

@app.websocket("/audio-websocket/ws/audio/{callId}")
async def websocket_audio_endpoint(websocket: WebSocket, callId: str):
    await websocket.accept()
    print(f"callId: {callId}")

    vad_buffer = bytearray()
    transcription_buffer = bytearray()
    audio_padding_size = 640 * 1 # ~ 30ms audio data?


    transcription_service = TranscriptionService()

    def transcript():
        # print(len(transcription_buffer))
        transcribe_thread = threading.Thread(target=preprocess_transcribe_audio, kwargs={'data': bytes(transcription_buffer), 'transcription_callback': transcription_service.transcription_callback})
        transcription_buffer.clear()
        transcribe_thread.start()

    def complete_transcript():
        full_transcription = transcription_service.get_transcription_and_clear()
        print(f"Full transcript: {full_transcription}")
        # Send to LLM

        async def handle_async_stuff():
            request = {}
            request['transcript'] = call_manager.add_utterance_to_call(callId, full_transcription, 'user')
            request['interaction_type'] = 'user_message'
            request['response_id'] = 'test123'

            queue1 = asyncio.Queue()
            queue2 = asyncio.Queue()

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

    detector = SpeechDetector(transcription_callback=transcript, complete_callback=complete_transcript)

    vad_thread = threading.Thread(target=VADDetect, kwargs={'audio_buffer': audio_queue, 'callback': detector.silero_response})
    vad_thread.start()

    try:
        while True:
            data = await websocket.receive_bytes()
            
            transcription_buffer.extend(data)
            vad_buffer.extend(data)

            while(len(vad_buffer) >= audio_padding_size):
                frame = vad_buffer[:audio_padding_size]
                audio_queue.put(frame)
                vad_buffer = vad_buffer[audio_padding_size:]
    except WebSocketDisconnect:
        print(f"Websocket closed by client")
        print(f"Call history: {call_manager.get_utterances_for_call(callId)}")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()
        


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)