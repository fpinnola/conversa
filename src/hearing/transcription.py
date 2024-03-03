class TranscriptionService:
    def __init__(self):
        self.current_transcription = ""
        pass

    def transcription_callback(self, res):
        self.current_transcription += res

    def get_transcription_and_clear(self):
        res = self.current_transcription
        self.current_transcription = ""
        return res
    