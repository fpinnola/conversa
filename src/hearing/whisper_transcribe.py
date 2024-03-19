import whisper
import numpy as np
import torch

SILENCE_HALLUCINATIONS = ["Thank you.", "you"]

def select_device():
    # Check for CUDA availability
    if torch.cuda.is_available():
        return torch.device('cuda')
    else:
        return torch.device('cpu')

device = select_device()

print(f"Whisper using device {device}")

model = whisper.load_model("small.en", device=device)  # Load a Whisper model. Choose the model size that suits your needs.

audio_buffer = bytearray()

from utils.audio_ops import Int2Float

def is_hallucination(target_str):
    target_str_cleaned = target_str.strip()
    for s in SILENCE_HALLUCINATIONS:
        if s.strip() == target_str_cleaned:
            return True  # Found an exact match

    return False  # No match found

def preprocess_transcribe_audio(data: bytes, transcription_callback=None):
        print(len(data))
        try:
            # Transcribe the audio
            sound = np.frombuffer(data, dtype=np.int16)
            waveform = Int2Float(sound)
            result = model.transcribe(audio=waveform)
            if transcription_callback is not None and not is_hallucination(result["text"]):
                transcription_callback(result["text"])
        except Exception as e:
            print(f"Error transcribing audio: {e}")

