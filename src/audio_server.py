from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
from whisper_transcribe import transcribe_audio


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(process_audio_queue())
    yield

app = FastAPI(lifespan=lifespan)

# Global queue for audio data
audio_queue = asyncio.Queue()

async def process_audio_queue():
    while True:
        audio_data = await audio_queue.get()
        await transcribe_audio(audio_data)


@app.websocket("/audio-websocket/ws/audio/{callId}")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            print(data)
            # await audio_queue.put(data)
            # await websocket.send_text("Data received")
    except WebSocketDisconnect:
        print(f"Websocket closed by client")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()
        


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)