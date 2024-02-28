from collections import defaultdict
import queue
import collections
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from vad import VADDetect, VADDetectSync

app = FastAPI()

audio_queue = queue.Queue()

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

    def silero_response(res):
        if res == "Speech":
            if not is_speaking:
                is_paused = False
                is_speaking = True
        else:
            if is_speaking:
                # Trigger transcription if more than 90ms has passed and transcription buffer is not empty
                
                # Trigger LLM callback if more than 1s has passed
                pass

        print(res)

    vad_thread = threading.Thread(target=VADDetect, kwargs={'audio_buffer': audio_queue, 'callback': silero_response})
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