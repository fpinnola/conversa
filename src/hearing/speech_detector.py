import threading

class SpeechDetector:
    def __init__(self, transcription_callback, complete_callback=None, speech_callback=None, max_audio_padding=640*180):
        self.last_speech_timer = None
        self.llm_timer = None
        self.transcription_delay = 0.2
        self.llm_delay = 0.8
        self.is_speaking = False
        self.current_transcription = ''
        self.transcription_callback = transcription_callback
        self.complete_callback = complete_callback
        self.speech_callback = speech_callback
        self.audio_buffer = bytearray()
        self.max_audio_padding = max_audio_padding

    def reset_timers(self):
        if self.last_speech_timer is not None:
            self.last_speech_timer.cancel()
        if self.llm_timer is not None:
            self.llm_timer.cancel()
        
        self.last_speech_timer = threading.Timer(self.transcription_delay, self.transcription_callback, kwargs={'transcription_buffer': self.audio_buffer})
        self.llm_timer = threading.Timer(self.llm_delay, self.call_llm)

        self.last_speech_timer.start()
        self.llm_timer.start()

    def call_llm(self):
        self.is_speaking = False
        if self.complete_callback:
            self.complete_callback()

    def silero_response(self, val, prob):
        if val == "Speech":
            if not self.is_speaking:
                self.is_speaking = True
            self.reset_timers()

    def on_audio(self, audio: bytes):
        self.audio_buffer.extend(audio)
        if not self.is_speaking and len(self.audio_buffer) >= self.max_audio_padding:
            self.audio_buffer = self.audio_buffer[self.max_audio_padding:]