import threading
from hearing.whisper_transcribe import preprocess_transcribe_audio


class SpeechDetector:
    def __init__(self, complete_callback=None, speech_callback=None, max_audio_padding=640*180):
        self.last_speech_timer = None
        self.llm_timer = None
        self.transcription_delay = 0.2
        self.llm_delay = 4.0
        self.is_speaking = False
        self.current_transcription = ''
        self.complete_callback = complete_callback
        self.speech_callback = speech_callback
        self.audio_buffer = bytearray()
        self.max_audio_padding = max_audio_padding

    def test_trigger_transcript(self, transcription_buffer=None):
        print(f"trigger_transcript is speaking {self.is_speaking}  buffer len {len(transcription_buffer)}")
        if self.is_speaking:
            transcribe_thread = threading.Thread(target=preprocess_transcribe_audio, kwargs={'data': bytes(transcription_buffer), 'transcription_callback': self.transcription_complete})
            transcription_buffer.clear()
            transcribe_thread.start()

    def reset_timers(self):
        if self.last_speech_timer is not None:
            self.last_speech_timer.cancel()
        if self.llm_timer is not None:
            self.llm_timer.cancel()
        
        self.last_speech_timer = threading.Timer(self.transcription_delay, self.test_trigger_transcript, kwargs={'transcription_buffer': self.audio_buffer})
        self.llm_timer = threading.Timer(self.llm_delay, self.call_llm)

        self.last_speech_timer.start()
        self.llm_timer.start()

    def call_llm(self):
        self.is_speaking = False
        if self.complete_callback:
            self.complete_callback()

    def silero_response(self, val, prob):
        if val == "Speech":
            print(f"Speech detected {prob}")
            if not self.is_speaking:
                self.is_speaking = True
            self.reset_timers()

    def on_audio(self, audio: bytes):
        self.audio_buffer.extend(audio)
        if not self.is_speaking and len(self.audio_buffer) >= self.max_audio_padding:
            self.audio_buffer = self.audio_buffer[self.max_audio_padding:]

    def transcription_complete(self, res):
        self.current_transcription += res
        if self.estimate_end_of_query(res):
            self.reset_timers()
            self.call_llm()

    def get_transcription_and_clear(self):
        res = self.current_transcription
        self.current_transcription = ""
        return res
    
    def estimate_end_of_query(self, transcript_chunk):
        """
        Estimates whether a chunk of transcript text is likely the end of a query.
        
        Args:
        transcript_chunk (str): A chunk of text from the speech-to-text output.
        
        Returns:
        bool: True if it's likely the end of the query, False otherwise.
        """
        # List of conjunctions, fillers, or phrases that might indicate more to come
        continuation_cues = ['and', 'or', 'but', 'you know', 'so', 'um', 'uh']
        
        # Check for explicit continuation with '...'
        if transcript_chunk.strip().endswith('...'):
            return False

        # Check for ending punctuation, considering Whisper's behavior
        if transcript_chunk.strip().endswith('.'):
            # If the transcript ends with a '.', but the context suggests it's not a conclusive end
            words = transcript_chunk.strip().split()
            if len(words) < 3:  # Very short phrase ending with a '.', might not be conclusive
                return False
            if words[-2].lower() in continuation_cues:
                return False  # Ending with a continuation cue before the period
            
        # Check for ending punctuation
        if transcript_chunk.strip().endswith(('.', '?', '!')):
            return True
        
        # Check for continuation cues at the end of the chunk
        words = transcript_chunk.strip().split()
        if len(words) == 0:
            return False  # Empty input
        if words[-1].lower() in continuation_cues:
            return False
        
        # If the last word is cut off, we might be in the middle of speaking
        if words[-1][-1] == '-':
            return False
        
        # Default to not the end if none of the above conditions are met
        return False