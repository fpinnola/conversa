from collections import defaultdict
import queue
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from whisper_transcribe import accumulate_and_transcribe



app = FastAPI()

# This will store a queue.Queue for each callId.
# defaultdict will automatically create a new queue if the callId doesn't exist yet.
call_queues = defaultdict(queue.Queue)

# Lock for thread-safe operations on call_queues
queue_lock = threading.Lock()


@app.websocket("/audio-websocket/ws/audio/{callId}")
async def websocket_audio_endpoint(websocket: WebSocket, callId: str):
    await websocket.accept()
    print(f"callId: {callId}")
    with queue_lock:  # Ensure thread-safe access to the queues
        # No need to explicitly check if callId exists; defaultdict handles it.
        call_queue = call_queues[callId]
    
    try:
        while True:
            data = await websocket.receive_bytes()
            # Thread-safe as each queue is independent, but locking here to illustrate
            # If you plan to modify the dictionary itself, keep the lock.
            with queue_lock:
                call_queue.put(data)  # Add received data to the appropriate queue

    except WebSocketDisconnect:
        print(f"Websocket closed by client")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()
        


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)