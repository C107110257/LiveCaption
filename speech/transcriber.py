import numpy as np

from faster_whisper import WhisperModel
from Config.Config import *


class AudioTranscriber:

    def __init__(self):
        print(whisper_model)
        self.model = WhisperModel(
            whisper_model,
            device="cpu",
            compute_type="int8",
            cpu_threads=WHISPER_CPU_THREADS,
            num_workers=1,
        )

    def transcribe(self, audio):

        audio = np.mean(audio, axis=1).astype(np.float32)
        audio_duration = len(audio) / SAMPLE_RATE

        segments, _ = self.model.transcribe(
            audio,
            language="en",
            beam_size=BEAM_SIZE,
            vad_filter=True,
            condition_on_previous_text=True,
            word_timestamps=True,
        )

        words = []

        for seg in segments:
            if not seg.words:
                continue
            for w in seg.words:
                words.append({
                    "start": w.start,
                    "end": w.end,
                    "word": w.word,
                })

        trailing_silence = (
            audio_duration - words[-1]["end"]
            if words else audio_duration
        )

        return {
            "words": words,
            "trailing_silence": trailing_silence,
        }