import time

from speech.translator import OfflineTranslator
from Config.settings import (
    WINDOW_SECONDS,
    STEP_SECONDS,
    SILENCE_FLUSH_THRESHOLD,
    MIN_BUFFER_LEN_FOR_PUNCT_FLUSH,
    MIN_BUFFER_LEN_FOR_SILENCE_FLUSH,
    MAX_BUFFER_LEN,
)
from pipeline.state import (
    english_queue,
    chinese_queue,
    translator_ready_event,
)
import pipeline.state as state


# 滑動視窗裡「新內容」的起始時間點。
# 例如 window=6s、step=3s，代表每個視窗有 3 秒是上一輪已經
# 辨識過的重疊音訊，只有 start >= 3.0 的字才是這一輪真正的新內容。
NEW_AUDIO_CUTOFF = WINDOW_SECONDS - STEP_SECONDS


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