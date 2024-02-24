import whisper
import asyncio
from io import BytesIO

model = whisper.load_model("base")  # Load a Whisper model. Choose the model size that suits your needs.

async def transcribe_audio(audio_data: bytes):
    # Convert the byte data to a file-like object
    audio_file = BytesIO(audio_data)

    # Use Whisper to transcribe the audio
    result = model.transcribe(audio_file)
    
    # Log the transcription
    print("Transcription:", result["text"])

if __name__ == "__main__":
    # Example usage with dummy audio data
    asyncio.run(transcribe_audio(b"Your audio data here"))
