import queue
from threading import Thread

import webrtcvad

vad = webrtcvad.Vad()
vad.set_mode(3)

SAMPLE_RATE = 16000 # Sample rate in Hz
PROCESSING_DURATION_MS = 30  # Duration of audio segment to process each time in milliseconds
PROCESSING_BUFFER_SAMPLES = int(SAMPLE_RATE * PROCESSING_DURATION_MS / 1000)
PROCESSING_BUFFER_SIZE_BYTES = PROCESSING_BUFFER_SAMPLES * 2

class WebRTCVAD(Thread):
    def __init__(self, callback=None):
        super().__init__()
        self.audio_buffer = bytearray()
        self.callback = callback
        self.queue = queue.Queue()

    def add_data(self, bytes):
        self.audio_buffer.extend(bytes)
        self.queue.put(bytes)

    def detect_speech_experiment(self, audio_buffer: bytearray):
        if len(audio_buffer) >= PROCESSING_BUFFER_SIZE_BYTES:
            input_bytes = audio_buffer[:PROCESSING_BUFFER_SIZE_BYTES]

            if self.callback:
                if (vad.is_speech(input_bytes, SAMPLE_RATE)):
                    self.callback("Speech")
                else:
                    self.callback("None")


            resultant_buffer = audio_buffer[PROCESSING_BUFFER_SIZE_BYTES:]
            
        else:
            resultant_buffer = audio_buffer

        return resultant_buffer

    def run(self):
        audio_buffer = bytearray()
        while True:
            data = self.queue.get()
            audio_buffer.extend(data)
            audio_buffer = self.detect_speech_experiment(audio_buffer)
