import numpy as np
import torch
import time
from threading import Thread
import queue
from scipy.io.wavfile import write
import noisereduce as nr

# Load the VAD model
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                            model='silero_vad',
                            force_reload=False)

(get_speech_ts, _, read_audio, VADIterator, _) = utils

vad_iterator = VADIterator(model)

SAMPLE_RATE = 16000 # Sample rate in Hz
PROCESSING_DURATION_MS = 500  # Duration of audio segment to process each time in milliseconds
RETAIN_DURATION_MS = 0  # Duration of audio segment to retain after processing in milliseconds

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


INPUT_BYTES_BUFFER = 512 * 2 * 16

class SileroVad(Thread):
    def __init__(self, callback=None):
        super().__init__()
        self.audio_buffer = bytearray()
        self.callback = callback
        self.queue = queue.Queue()

    def add_data(self, bytes):
        self.audio_buffer.extend(bytes)
        self.queue.put(bytes)

    def detect_speech_experiment(self, audio_buffer: bytearray):
        if len(audio_buffer) >= INPUT_BYTES_BUFFER:
            first_bytes = audio_buffer[:INPUT_BYTES_BUFFER]
            # print(len(first_bytes))

            newsound= np.frombuffer(first_bytes,np.int16)
            # print(newsound.shape)
            # reduced_noise = nr.reduce_noise(y=newsound, sr=SAMPLE_RATE)
            
            # audio_stream_tensor =  torch.from_numpy(newsound.squeeze()).astype('float32')
            audio_stream_tensor = Int2Float(newsound)
            # print(audio_stream_tensor.shape)
            if audio_stream_tensor.ndim > 1:
                audio_stream_tensor = audio_stream_tensor.squeeze()
            # print(audio_stream_tensor.dtype)
            speech_dict = vad_iterator(audio_stream_tensor, return_seconds=True)
            if speech_dict:
                print(speech_dict, end=' ')
            else:
                print('No speech')

            resultant_buffer = audio_buffer[INPUT_BYTES_BUFFER:]
            
        else:
            resultant_buffer = audio_buffer

        return resultant_buffer

    def detect_speech(self, audio_buffer: bytearray):
        if len(audio_buffer) > PROCESSING_BUFFER_SIZE_BYTES:
            
            audio_buffer = audio_buffer[-PROCESSING_BUFFER_SIZE_BYTES:]
            newsound= np.frombuffer(audio_buffer,np.int16)
            reduced_noise = nr.reduce_noise(y=newsound, sr=SAMPLE_RATE)
            
            # audio_stream_tensor =  torch.from_numpy(newsound.squeeze()).astype('float32')
            audio_stream_tensor = Int2Float(newsound)
            if audio_stream_tensor.ndim > 1:
                audio_stream_tensor = audio_stream_tensor.squeeze()
            print(audio_stream_tensor.dtype)
            start_time = time.time()
            window_size_samples = 512
            speech_dict = None
            for i in range(0, len(audio_stream_tensor), window_size_samples):
                print(audio_stream_tensor[i: i+window_size_samples].shape)
                speech_dict = vad_iterator(audio_stream_tensor[i: i+ window_size_samples], return_seconds=True)
                if speech_dict:
                    print(speech_dict, end=' ')
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            print(f'speech_timestamps {speech_dict}, duration {duration_ms} timestep {len(audio_buffer) / 2 / 16}')
            if RETAIN_BUFFER_SIZE_BYTES <= 0:
                audio_buffer = bytearray()
            else:
                audio_buffer = audio_buffer[-RETAIN_BUFFER_SIZE_BYTES:]
        return audio_buffer