import os
from abc import ABC, abstractmethod

beginSentence = os.environ.get('AGENT_PROMPT')
agentPrompt = os.environ.get('AGENT_INITIATE')

class LlmClient(ABC):
    def __init__(self):
        self.beginSentence = beginSentence
        self.agentPrompt = agentPrompt
    
    @abstractmethod
    def draft_begin_message(self):
        pass

    @abstractmethod
    async def draft_response(self, request):   
        pass   