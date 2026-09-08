import soundcard as sc
import numpy as np

from collections import deque
from queue import Full

from Config.Config import SAMPLE_RATE, WINDOW_SECONDS, STEP_SECONDS


class AudioRecorder:

    def __init__(self, queue):

        self.queue = queue

        speaker = sc.default_speaker()

        self.mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)

    def run(self):

        buffer = deque(maxlen=WINDOW_SECONDS // STEP_SECONDS)

        with self.mic.recorder(samplerate=SAMPLE_RATE) as recorder:

            while True:

                chunk = recorder.record(numframes=SAMPLE_RATE * STEP_SECONDS)

                buffer.append(chunk)

                if len(buffer) < buffer.maxlen:
                    continue

                audio = np.concatenate(list(buffer), axis=0)

                volume = np.abs(audio).mean()

                if volume < 0.001:
                    continue

                try:

                    self.queue.put_nowait(audio)

                except Full:

                    try:
                        self.queue.get_nowait()
                    except Exception:
                        pass

                    self.queue.put_nowait(audio)
