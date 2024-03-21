# Conversa
## Overview
Conversa is an open source platform for devleping conversational AI Agents with speech. Conversa handles the speech transcription, speech synthesis, and other audio processing to deliver fast, high quality audio conversations with your agents. Conversa queries your backend for responses from your LLM, allowing you to focus entirely on your LLM.
![Untitled Diagram drawio (1)](https://github.com/fpinnola/conversa/assets/45111715/35cb08c8-e419-4449-84da-17ba55b3cbc9)

## Getting Started
Build the docker image
```
docker build -t conversa .
```

Setup a file for enviornment variables, using the `sample-env.list` file.

Run the docker image
```
docker run --env-file=sample-env.list -p 8000:8000 conversa
```


## Implementation Details
![Group 10 (1)](https://github.com/fpinnola/conversa/assets/45111715/64896766-a442-4a4e-8b1e-cfaa1ec2d905)

## Next Steps
The main focus now is to reduce the speech to speech latency of the conversations. This is measured by the time from the end of the user's speech to the start of the agent's speech on the user client.

Future improvements inlcude adding a Twilio integration and adding support for other Speech systhesis services.
