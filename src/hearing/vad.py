import torch
import numpy as np
from utils.audio_ops import Int2Float

async def vad_detect(audio_queue, threshold=0.75, callback=None):

    # Load Silero VAD Model
    model, _ = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                            model='silero_vad',
                            force_reload=False)


    window_size_bytes = 512 * 2
    window_size_samples = 512 

    audio_buffer = bytearray()

    while True:
        data = await audio_queue.get()
        audio_buffer.extend(data)
        speech_probs2 = []
        if len(audio_buffer) >= window_size_bytes:
            first_N_bytes = audio_buffer[:window_size_bytes]
    
            numpy_array = np.frombuffer(first_N_bytes, dtype=np.int16)
            wav = Int2Float(numpy_array)
            
            # Remove the N first bytes from the original bytearray
            del audio_buffer[:window_size_bytes]
            for i in range(0, len(wav), window_size_samples):
                chunk = wav[i: i+window_size_samples]
                if len(chunk) < window_size_samples:
                    break
                speech_prob = model(chunk, 16000).item()
                speech_probs2.append(speech_prob)
                if callback is not None:
                    if speech_prob >= threshold:
                        callback("Speech", speech_prob)
                    else:
                        callback("None", speech_prob)

        audio_queue.task_done()
