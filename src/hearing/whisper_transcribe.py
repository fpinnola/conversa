import whisper
import numpy as np
import asyncio
import torch

def select_device():
    # Check for CUDA availability
    if torch.cuda.is_available():
        return torch.device('cuda')
    else:
        return torch.device('cpu')

device = select_device()

print(f"Using device {device}")

model = whisper.load_model("base.en", device=device)  # Load a Whisper model. Choose the model size that suits your needs.

audio_buffer = bytearray()


def convert_uint8_to_waveform(data: bytes, sample_rate: int = 16000):
    # Assuming data is 16-bit PCM, convert UInt8 array to int16
    waveform = np.frombuffer(data, dtype=np.int16)
    waveform = waveform.astype(np.float32) / np.iinfo(np.int16).max
    return waveform

async def transcribe_audio(data: bytes, sample_rate: int = 16000):
    try:
        # Transcribe the audio
        result = model.transcribe(audio=data)
        print("Transcription:", result["text"])
    except Exception as e:
        print(f"Error transcribing audio: {e}")

def preprocess_transcribe_audio(data: bytes, transcription_callback=None, sample_rate: int = 16000):
        try:
            # Transcribe the audio
            waveform = convert_uint8_to_waveform(bytes(data), sample_rate)
            result = model.transcribe(audio=waveform)
            if transcription_callback is not None:
                transcription_callback(result["text"])
        except Exception as e:
            print(f"Error transcribing audio: {e}")

async def accumulate_and_transcribe(data: bytes, threshold: int = 16000 * 5, sample_rate=16000):
    global audio_buffer
    audio_buffer += data  # Append new data to the buffer

    overlap = int(threshold * 0.2)  # 20% overlap
    if len(audio_buffer) >= threshold:
        # Process up to the threshold minus overlap
        to_process = audio_buffer[:threshold-overlap]
        waveform = convert_uint8_to_waveform(bytes(to_process), sample_rate)
        asyncio.create_task(transcribe_audio(waveform, sample_rate))

        # Keep the overlap for the next chunk
        audio_buffer = audio_buffer[threshold-overlap:]



if __name__ == "__main__":
    # Example usage with dummy audio data
    # asyncio.run(transcribe_audio(b"Your audio data here"))
    print(f"cuda: {torch.cuda.is_available()}")
