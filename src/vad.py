# Code based on example from: https://github.com/snakers4/silero-vad/blob/master/examples/microphone_and_webRTC_integration/microphone_and_webRTC_integration.py

import collections, queue
import numpy as np
import pyaudio
import webrtcvad
import torch
import torchaudio


# load silero VAD
torchaudio.set_audio_backend("soundfile")
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                model="silero_vad",
                                force_reload=False)
(get_speech_ts,_,_, _,_) = utils

class Audio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = pyaudio.paInt16
    # Network/VAD rate-space
    RATE_PROCESS = 16000
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50

    def __init__(self, audio_buffer=None, callback=None, input_rate=RATE_PROCESS):
        if callback is None: callback = lambda in_data: self.buffer_queue.put(in_data)

        self.input_rate = input_rate
        self.sample_rate = self.RATE_PROCESS
        self.block_size = int(self.RATE_PROCESS / float(self.BLOCKS_PER_SECOND))
        self.block_size_input = int(self.input_rate / float(self.BLOCKS_PER_SECOND))

        if audio_buffer is not None:
            print(f"audio buffer {audio_buffer}")
            self.buffer_queue = audio_buffer
            return

    def read(self):
        """Return a block of audio data, blocking if necessary."""
        try:
            return self.buffer_queue.get(timeout=1)
        except:
            print('Error')
            return bytes()

    def destroy(self):
        pass

    frame_duration_ms = property(lambda self: 1000 * self.block_size // self.sample_rate)


class VADAudio(Audio):
    """Filter & segment audio with voice activity detection."""

    def __init__(self, audio_buffer=None, aggressiveness=3, input_rate=None, ):
        super().__init__(input_rate=input_rate, audio_buffer=audio_buffer)
        self.vad = webrtcvad.Vad(aggressiveness)

    def frame_generator(self):
        """Generator that yields all audio frames from microphone."""
        if self.input_rate == self.RATE_PROCESS:
            while True:
                yield self.read()
        else:
            raise Exception("Resampling required")

    def vad_collector(self, padding_ms=300, ratio=0.75, frames=None):
        """Generator that yields series of consecutive audio frames comprising each utterence, separated by yielding a single None.
            Determines voice activity by ratio of frames in padding_ms. Uses a buffer to include padding_ms prior to being triggered.
            Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                      |---utterence---|        |---utterence---|
        """
        if frames is None: frames = self.frame_generator()

        num_padding_frames = padding_ms // self.frame_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False
        for frame in frames:
            if len(frame) < 640:
                return

            is_speech = self.vad.is_speech(frame, self.sample_rate)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > ratio * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()

def VADDetect(audio_buffer=None, webRTC_aggressiveness=3, sample_rate=16000, callback=None):
    # Start audio with VAD
    vad_audio = VADAudio(audio_buffer=audio_buffer, aggressiveness=webRTC_aggressiveness,
                         input_rate=sample_rate)


    frames = vad_audio.vad_collector(padding_ms=25)

    print(f"frames {frames}")

    # Stream from microphone to DeepSpeech using VAD
    spinner = None
    wav_data = bytearray()

    for frame in frames:
        if frame is not None:
            if spinner: spinner.start()

            wav_data.extend(frame)
        else:
            if spinner: spinner.stop()
            newsound= np.frombuffer(wav_data,np.int16)
            audio_float32=Int2Float(newsound)
            time_stamps =get_speech_ts(audio_float32, model)

            if(len(time_stamps)>0):
                if callback:
                    callback("Speech")
                # print("silero VAD has detected a possible speech")
            else:
                if callback:
                    callback("Noise")
                # print("silero VAD has detected a noise")
            print()
            wav_data = bytearray()


def VADDetectSync(audio_buffer=None, webRTC_aggressiveness=3, sample_rate=16000, callback=None):
    # print(len(audio_buffer))
    newsound = np.frombuffer(audio_buffer, np.int16)
    audio_float32=Int2Float(newsound)
    time_stamps = get_speech_ts(audio_float32, model)

    if (len(time_stamps) > 0):
        if callback:
            callback("Sound")
        else:
            print("silero VAD has detected speech")
    else:
        if callback:
            callback("Noise")
        else:
            print("silero VAD has detected noise")

def Int2Float(sound):
    _sound = np.copy(sound)
    abs_max = np.abs(_sound).max()
    _sound = _sound.astype('float32')
    if abs_max > 0:
        _sound *= 1/abs_max
    audio_float32 = torch.from_numpy(_sound.squeeze())
    return audio_float32

import asyncio


async def add_to_queue_test(buff):
    while True:
        await asyncio.sleep(1)
        print('adding to queue')
        buff.put(b'444')

async def run_jobs(audio_queue):
    task = asyncio.run(add_to_queue_test(audio_queue))


if __name__ == '__main__':
    DEFAULT_SAMPLE_RATE = 16000
    audio_queue = queue.Queue()
    audio_queue.put(b'123')
    run_jobs(audio_queue)
    VADDetect(audio_queue)
    print(audio_queue.get())