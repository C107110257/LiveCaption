# speech/transcriber.py
import numpy as np

from faster_whisper import WhisperModel
from Config.Config import BEAM_SIZE, MODEL_PATH_base


class AudioTranscriber:

    def __init__(self):
        print(MODEL_PATH_base)
        self.model = WhisperModel(MODEL_PATH_base, device="cpu", compute_type="int8")

    def transcribe(self, audio):

        audio = np.mean(audio, axis=1).astype(np.float32)

        segments, _ = self.model.transcribe(
            audio,
            language="en",
            beam_size=BEAM_SIZE,
            vad_filter=True,
            condition_on_previous_text=True,
        )

        return [
            {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
            for seg in segments
            if seg.text.strip()
        ]
