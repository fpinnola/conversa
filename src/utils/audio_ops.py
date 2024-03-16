from scipy.io.wavfile import write
import numpy as np
import torch

def Int2Float(sound):
    audio_float32 = torch.from_numpy(sound.astype(np.float32) / 32768.0)
    return audio_float32


def write_to_wav(name: str, audio_buffer: bytearray):
    narray = np.frombuffer(audio_buffer, dtype=np.int16)
    write(name + '.wav', 16000, narray)

def write_bytes(name: str, audio_buffer: bytearray):
    narray = np.frombuffer(audio_buffer, dtype=np.int16)
    float_array = Int2Float(narray)
    torch.save(float_array, name + '.pt')