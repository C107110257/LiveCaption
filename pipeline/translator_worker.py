import time

from speech.translator import OfflineTranslator
from Config.Config import WINDOW_SECONDS, STEP_SECONDS
from pipeline.state import (
    english_queue,
    chinese_queue,
    translator_ready_event,
)
import pipeline.state as state


NEW_AUDIO_CUTOFF = WINDOW_SECONDS - STEP_SECONDS
SILENCE_FLUSH_THRESHOLD = 0.5
MIN_BUFFER_LEN_FOR_PUNCT_FLUSH = 60
MIN_BUFFER_LEN_FOR_SILENCE_FLUSH = 20
MAX_BUFFER_LEN = 120


def load_translator(status_callback):
    state.translator = OfflineTranslator(status_callback=status_callback)
    translator_ready_event.set()


def translate_loop():

    translator_ready_event.wait()

    sentence_buffer = ""
    is_first_window = True

    while True:

        result = english_queue.get()

        try:
            words = result["words"]
            trailing_silence = result["trailing_silence"]

            if not words:
                continue

            if is_first_window:
                new_words = words
                is_first_window = False
            else:
                new_words = [w for w in words if w["start"] >= NEW_AUDIO_CUTOFF]

            english_text = "".join(w["word"] for w in new_words).strip()

            if not english_text:
                continue

            sentence_buffer += " " + english_text
            sentence_buffer = sentence_buffer.strip()

            has_real_pause = trailing_silence > SILENCE_FLUSH_THRESHOLD

            should_flush = (
                (sentence_buffer.endswith((".", "?", "!")) and len(sentence_buffer) >= MIN_BUFFER_LEN_FOR_PUNCT_FLUSH)
                or (has_real_pause and len(sentence_buffer) >= MIN_BUFFER_LEN_FOR_SILENCE_FLUSH)
                or len(sentence_buffer) > MAX_BUFFER_LEN
            )

            if not should_flush:
                print(f"buffer: {sentence_buffer}")
                continue

            start = time.perf_counter()
            chinese_text = state.translator.translate(sentence_buffer)
            cost = time.perf_counter() - start
            print(f"[Translator] {cost:.2f}s")

            chinese_queue.put((sentence_buffer, chinese_text))
            sentence_buffer = ""

        except Exception as ex:
            print(f"[Translator] {ex}")

        finally:
            english_queue.task_done()