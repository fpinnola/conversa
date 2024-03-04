import uuid
from pydantic import BaseModel

class CreateCallBody(BaseModel):
    voiceId: str


# TODO: integrate with DB
class CallManager:
    def __init__(self):
        self.calls = {}
        pass

    def get_call_properties(self, callId):
        if callId not in self.calls:
            return None
        return self.calls['callId']['properties']


    def add_utterance_to_call(self, callId, text, role):
        if callId not in self.calls:
            self.calls[callId] = { 'utterances': [] }
        
        self.calls[callId]['utterances'].append({'role': role, 'content': text})

        return self.calls[callId]['utterances']

    def get_utterances_for_call(self, callId):
        if callId not in self.calls:
            return []
        
        return self.calls[callId]['utterances']
    
    def generate_unique_call_id(self):
        new_id = ''
        while True:
            new_id = str(uuid.uuid4())
            if new_id not in self.calls:
                return new_id
    
    def create_call(self, callProperties: CreateCallBody):
        callId = self.generate_unique_call_id()
        print(f"callId: {callId}")
        call = {
            'properties': callProperties,
            'callId': callId
        }
        self.calls['callId'] = call
        return call