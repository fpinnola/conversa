# Conversa
## Overview
Conversa is an open source platform for devleping conversational AI Agents with speech. Conversa handles the speech transcription, speech synthesis, and other audio processing to deliver fast, high quality audio conversations with your agents. Conversa queries your backend for responses from your LLM, allowing you to focus entirely on your LLM.

## Getting Started
### Build Docker
Build the docker image
```
docker build -t conversa .
```
### Environment setup

Setup a file for enviornment variables, using the `sample-env.list` file.

Two properties are exposed to setup the system prompts for the LLM:
- AGENT_PROMPT: the initial message the agent will say when the conversation is started
- AGENT_INITIATE: the system prompt for the agent

### Run Docker
Run the docker image
```
docker run --env-file=sample-env.list -p 8000:8000 conversa
```

### Run demo application
You can find a demo application using the Conversa web client [here](https://github.com/fpinnola/conversa-js-client/tree/main/example)

## Implementation Details

![Group 10 (1)](https://github.com/fpinnola/conversa/assets/45111715/64896766-a442-4a4e-8b1e-cfaa1ec2d905)

## Next Steps
The main focus now is to reduce the speech to speech latency of the conversations. This is measured by the time from the end of the user's speech to the start of the agent's speech on the user client.

Another remaining feature is to open a websocket channel for custom backends to connect to, which will receive a user's transcription and will return the agent's response. This will allow custom services to handle agent response logic using whichever models and logic they prefer.


Future improvements inlcude adding a Twilio integration and adding support for other Speech systhesis services.
