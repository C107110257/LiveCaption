from queue import Queue
import threading
import time
import warnings
import re

from speech.translator import OfflineTranslator

warnings.filterwarnings("ignore", message="data discontinuity in recording")

from audio.recorder import AudioRecorder
from speech.transcriber import AudioTranscriber
from ui.console import ConsoleUI
from Config.Config import *
from ui.caption_window import CaptionWindow
from difflib import SequenceMatcher

caption_window = CaptionWindow()

audio_queue = Queue(maxsize=MAX_AUDIO_QUEUE)

english_queue = Queue()

chinese_queue = Queue()

recorder = AudioRecorder(audio_queue)

translator = None

# def monitor_loop():

#     while True:

#         print(
#             f"Audio={audio_queue.qsize()} "
#             f"EN={english_queue.qsize()} "
#             f"ZH={chinese_queue.qsize()}"
#         )


#         time.sleep(1)
def is_similar(a, b):

    if not a or not b:
        return False

    return SequenceMatcher(None, a, b).ratio() > 0.85

def _normalize_word(w):
    return re.sub(r"[^\w']", "", w.lower())

def remove_overlap(current, previous, min_overlap_words=2, similarity_threshold=0.8):

    if not previous:
        return current

    current_words = current.split()
    previous_words = previous.split()

    # 用去除標點後的版本做比對，但保留原始 current_words 用來組回傳結果
    current_norm = [_normalize_word(w) for w in current_words]
    previous_norm = [_normalize_word(w) for w in previous_words]

    matcher = SequenceMatcher(None, previous_norm, current_norm)

    match = matcher.find_longest_match(
        0, len(previous_norm),
        0, len(current_norm)
    )

    if match.size >= min_overlap_words:
        tail_ratio = (match.a + match.size) / len(previous_norm) if previous_norm else 0
        head_ratio = match.b / len(current_norm) if current_norm else 1

        is_tail_of_previous = tail_ratio > 0.6
        is_head_of_current = head_ratio < 0.4

        if is_tail_of_previous and is_head_of_current:
            remainder = current_words[match.b + match.size:]
            return " ".join(remainder)

    overlap_ratio = match.size / max(len(current_norm), 1)
    if overlap_ratio > similarity_threshold:
        return ""

    return current

def transcribe_loop(worker_name):

    transcriber = AudioTranscriber()

    while True:

        audio = audio_queue.get()

        try:

            start = time.perf_counter()

            text = transcriber.transcribe(audio)

            cost = time.perf_counter() - start

            print(f"[{worker_name}] {cost:.2f}s")

            english_queue.put(text)

        except Exception as ex:

            print(f"[{worker_name}] {ex}")

        finally:

            audio_queue.task_done()

NEW_AUDIO_CUTOFF = WINDOW_SECONDS - STEP_SECONDS
SILENCE_FLUSH_THRESHOLD = 0.5   # 視窗結尾若超過這麼久沒新字，視為真正停頓
MIN_BUFFER_LEN_FOR_PUNCT_FLUSH = 60   # 從 40 提高到 60，減少短碎句誤觸發
MIN_BUFFER_LEN_FOR_SILENCE_FLUSH = 20  # 停頓觸發時，門檻可以低一點
MAX_BUFFER_LEN = 120


def translate_loop():

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
            chinese_text = translator.translate(sentence_buffer)
            cost = time.perf_counter() - start
            print(f"[Translator] {cost:.2f}s")

            chinese_queue.put((sentence_buffer, chinese_text))
            sentence_buffer = ""

        except Exception as ex:
            print(f"[Translator] {ex}")

        finally:
            english_queue.task_done()


def ui_loop():

    while True:

        english_text, chinese_text = chinese_queue.get()

        try:

            caption_window.update_text(english_text, chinese_text)
            ConsoleUI.show(
                f"==================================================\n"
                f"  EN: {english_text}\n"
                f"  ZH: {chinese_text}\n"
                f"==================================================\n"
            )

        finally:

            chinese_queue.task_done()

def startup():

    global translator

    translator = OfflineTranslator(
        status_callback=caption_window.update_text
    )

    threading.Thread(
        name="Recorder",
        target=recorder.run,
        daemon=True,
    ).start()

    for i in range(WORKER_COUNT):
        threading.Thread(
            name=f"Transcriber-{i+1}",
            target=transcribe_loop,
            args=(f"Whisper-{i+1}",),
            daemon=True,
        ).start()

    threading.Thread(
        name="Translator",
        target=translate_loop,
        daemon=True,
    ).start()

    threading.Thread(
        name="UI",
        target=ui_loop,
        daemon=True,
    ).start()

    caption_window.update_text(
        "系統已就緒",
        "Ready",
        "#00FF66"
    )

def main():

    threading.Thread(
        target=startup,
        daemon=True,
    ).start()

    caption_window.run()


if __name__ == "__main__":
    main()
