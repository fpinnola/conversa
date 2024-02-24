from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
from src.whisper_transcribe import transcribe_audio

app = FastAPI()

# Global queue for audio data
audio_queue = asyncio.Queue()

async def process_audio_queue():
    while True:
        audio_data = await audio_queue.get()
        await transcribe_audio(audio_data)

@app.on_event("startup")
async def startup_event():
    # Start the audio processing task
    asyncio.create_task(process_audio_queue())

@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            await audio_queue.put(data)
            await websocket.send_text("Data received")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)