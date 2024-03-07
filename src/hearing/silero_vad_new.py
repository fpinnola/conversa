import numpy as np
import torch

# Load the VAD model
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                            model='silero_vad',
                            force_reload=False)

(get_speech_ts, _, read_audio, _, _) = utils

SAMPLE_RATE = 16000 # Sample rate in Hz
PROCESSING_DURATION_MS = 450  # Duration of audio segment to process each time in milliseconds
RETAIN_DURATION_MS = 350  # Duration of audio segment to retain after processing in milliseconds

# Calculate buffer sizes in bytes (since int16 = 2 bytes per sample)
PROCESSING_BUFFER_SAMPLES = int(SAMPLE_RATE * PROCESSING_DURATION_MS / 1000)
RETAIN_BUFFER_SAMPLES = int(SAMPLE_RATE * RETAIN_DURATION_MS / 1000)

# Note: Multiply by 2 for the byte length because each sample is 2 bytes (int16)
PROCESSING_BUFFER_SIZE_BYTES = PROCESSING_BUFFER_SAMPLES * 2
RETAIN_BUFFER_SIZE_BYTES = RETAIN_BUFFER_SAMPLES * 2

def Int2Float(sound):
    _sound = np.copy(sound)
    abs_max = np.abs(_sound).max()
    _sound = _sound.astype('float32')
    if abs_max > 0:
        _sound *= 1/abs_max
    audio_float32 = torch.from_numpy(_sound.squeeze())
    return audio_float32


def detect_speech(audio_buffer: bytearray, callback=None):
    if len(audio_buffer) > PROCESSING_BUFFER_SIZE_BYTES:
        audio_buffer = audio_buffer[-PROCESSING_BUFFER_SIZE_BYTES:]
        newsound= np.frombuffer(audio_buffer,np.int16)
        audio_stream_tensor = Int2Float(newsound)
        if audio_stream_tensor.ndim > 1:
            audio_stream_tensor = audio_stream_tensor.squeeze()
        speech_timestamps = get_speech_ts(audio_stream_tensor, model)
        print(f'speech_timestamps {speech_timestamps}')
        audio_buffer = audio_buffer[-RETAIN_BUFFER_SIZE_BYTES:]
        if callback is not None and len(speech_timestamps) > 0:
            callback("Speech detected!")
    return audio_buffer