from collections import defaultdict
import queue
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from vad import VADDetect

app = FastAPI()

audio_queue = queue.Queue()

@app.websocket("/audio-websocket/ws/audio/{callId}")
async def websocket_audio_endpoint(websocket: WebSocket, callId: str):
    await websocket.accept()
    print(f"callId: {callId}")

    audio_buffer = bytearray()
    frame_size = 640

    vad_thread = threading.Thread(target=VADDetect, args=(audio_queue,))
    vad_thread.start()

    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)

            while(len(audio_buffer) >= frame_size):
                frame = audio_buffer[:frame_size]
                audio_queue.put(frame)
                audio_buffer = audio_buffer[frame_size:]
    except WebSocketDisconnect:
        print(f"Websocket closed by client")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()
        


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)