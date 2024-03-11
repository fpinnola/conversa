import os
import requests

def get_elevenlabs_voices():
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

    url = 'https://api.elevenlabs.io/v1/voices'

    response = requests.request("GET", url, headers={
        "xi_api_key": ELEVENLABS_API_KEY,
    })

    data = response.json()

    filtered_list = [
        { ('voiceId' if k == 'voice_id' else 'metadata' if k == 'labels' else k): v
            for k, v in d.items() if k in ('voice_id', 'name', 'labels')} for d in data["voices"]
    ]

    
    return filtered_list

