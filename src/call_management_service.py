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
    

if __name__ == "__main__":
    from llm import LlmClient
    from dotenv import load_dotenv
    load_dotenv()
    

    call_manager = CallManager()
    llm_client = LlmClient()
    request = {}
    request['transcript'] = call_manager.add_utterance_to_call('test123', 'Hi my name is frank. I am feeling ok', 'user')
    request['interaction_type'] = 'user_message'
    request['response_id'] = 'test123'
    # prompt = llm_client.prepare_prompt(request)
    response_generator = llm_client.draft_response(request)
    # print(prompt)
    full_content = ""
    for chunk in response_generator:
        if chunk['content']:  # If there's content, process or display it
            print(chunk['content'])
            full_content += chunk['content']
        if chunk['content_complete']:
            print("Finalizing response handling.")
            break
    print(f"full content: {full_content}")
