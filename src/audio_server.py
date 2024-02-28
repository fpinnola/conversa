from collections import defaultdict
import queue
import collections
import threading
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from vad import VADDetect, VADDetectSync

app = FastAPI()

audio_queue = queue.Queue()

class SpeechDetector:
    def __init__(self):
        self.last_speech_timer = None
        self.llm_timer = None
        self.transcription_delay = 1.0
        self.llm_delay = 3.0
        self.is_speaking = False
        self.is_paused = True
        self.last_speech = 0
        self.current_transcription = ''

    def reset_timers(self):
        if self.last_speech_timer is not None:
            self.last_speech_timer.cancel()
        if self.llm_timer is not None:
            self.llm_timer.cancel()
        
        self.last_speech_timer = threading.Timer(self.transcription_delay, self.trigger_transcription)
        self.llm_timer = threading.Timer(self.llm_delay, self.call_llm)

        self.last_speech_timer.start()
        self.llm_timer.start()

    def trigger_transcription(self):
        print("Trigger transcription")
        self.is_paused = True
    
    def call_llm(self):
        print("Call LLM")
        self.is_speaking = False

    def silero_response(self, res):
        print(res)
        if res == "Speech":
            if not self.is_speaking:
                self.is_paused = False
                self.is_speaking = True
            self.reset_timers()



@app.websocket("/audio-websocket/ws/audio/{callId}")
async def websocket_audio_endpoint(websocket: WebSocket, callId: str):
    await websocket.accept()
    print(f"callId: {callId}")

    vad_buffer = bytearray()
    transcription_buffer = bytearray()
    audio_padding_size = 640 * 1 # ~ 30ms audio data?



    is_speaking = False
    is_paused = True
    last_speech = 0

    current_transcription = ''

    detector = SpeechDetector()

    vad_thread = threading.Thread(target=VADDetect, kwargs={'audio_buffer': audio_queue, 'callback': detector.silero_response})
    vad_thread.start()

    try:
        while True:
            data = await websocket.receive_bytes()

            if not is_speaking and len(transcription_buffer) > audio_padding_size :
                transcription_buffer = transcription_buffer[audio_padding_size:]
            
            transcription_buffer.extend(data)
            vad_buffer.extend(data)

            while(len(vad_buffer) >= audio_padding_size):
                frame = vad_buffer[:audio_padding_size]
                audio_queue.put(frame)
                vad_buffer = vad_buffer[audio_padding_size:]
    except WebSocketDisconnect:
        print(f"Websocket closed by client")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()
        


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)