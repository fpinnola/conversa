class CallManager:
    def __init__(self):
        self.calls = {}
        pass

    def add_utterance_to_call(self, callId, text, role):
        if callId not in self.calls:
            self.calls[callId] = { 'utterances': [] }
        
        self.calls[callId]['utterances'].append({'role': role, 'content': text})

        return self.calls[callId]['utterances']

    def get_utterances_for_call(self, callId):
        if callId not in self.calls:
            return []
        
        return self.calls[callId]['utterances']
    
