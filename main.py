from queue import Queue
import threading
import time
import warnings

from speech.translator import OfflineTranslator

warnings.filterwarnings("ignore", message="data discontinuity in recording")

from audio.recorder import AudioRecorder
from speech.transcriber import AudioTranscriber
from ui.console import ConsoleUI
from Config.Config import MAX_AUDIO_QUEUE, WORKER_COUNT
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


# def remove_overlap(current, previous):

#     if not previous:
#         return current

#     current_words = current.split()
#     previous_words = previous.split()

#     current_lower = [w.lower() for w in current_words]
#     previous_lower = [w.lower() for w in previous_words]

#     max_overlap = min(
#         len(current_words),
#         len(previous_words)
#     )

#     # 尾巴接頭
#     for size in range(max_overlap, 2, -1):

#         if (
#             previous_lower[-size:]
#             ==
#             current_lower[:size]
#         ):
#             return " ".join(
#                 current_words[size:]
#             )

#     # 整段重複
#     for size in range(max_overlap, 3, -1):

#         if (
#             current_lower[:size]
#             ==
#             previous_lower[:size]
#         ):
#             return " ".join(
#                 current_words[size:]
#             )

#     return current

def remove_overlap(current, previous, min_overlap_words=2, similarity_threshold=0.8):

    if not previous:
        return current

    current_words = current.split()
    previous_words = previous.split()

    current_lower = [w.lower() for w in current_words]
    previous_lower = [w.lower() for w in previous_words]

    matcher = SequenceMatcher(None, previous_lower, current_lower)

    # 找出 previous 與 current 之間最長的連續匹配區塊
    match = matcher.find_longest_match(
        0, len(previous_lower),
        0, len(current_lower)
    )

    # match.b 是這段匹配在 current 裡的起始 index
    # match.b + match.size 是匹配結束的位置（也就是重疊內容結束的地方）
    if match.size >= min_overlap_words:
        # 確認這段匹配大致落在 previous 的尾巴、current 的開頭
        # （避免抓到句子中間偶然重複的詞，例如常見的 "the", "and"）
        tail_ratio = (match.a + match.size) / len(previous_lower)
        head_ratio = match.b / len(current_lower) if len(current_lower) else 1

        is_tail_of_previous = tail_ratio > 0.6
        is_head_of_current = head_ratio < 0.4

        if is_tail_of_previous and is_head_of_current:
            remainder = current_words[match.b + match.size:]
            return " ".join(remainder)

    # 退一步：檢查是否整段幾乎相同（例如只是重新辨識、幾乎沒有新內容）
    overlap_ratio = match.size / max(len(current_lower), 1)
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


def translate_loop():

    last_text = ""

    sentence_buffer = ""

    while True:

        english_segments = english_queue.get()

        try:

            english_text = " ".join(seg["text"] for seg in english_segments).strip()

            if not english_text:
                continue

            if len(english_text) < 15:
                continue

            if is_similar(english_text, last_text):
                continue
            # 保存 Whisper 原始輸出
            original_text = english_text

            # 去除重疊內容
            english_text = remove_overlap(english_text, last_text)

            if not english_text:
                continue

            last_text = original_text

            sentence_buffer += " " + english_text

            sentence_buffer = sentence_buffer.strip()

            # 還沒形成完整句子
            MIN_BUFFER_LEN_FOR_PUNCT_FLUSH = 40  # 至少要有這麼多字才允許用標點提前送出

            if not (
                (sentence_buffer.endswith((".", "?", "!")) and len(sentence_buffer) >= MIN_BUFFER_LEN_FOR_PUNCT_FLUSH)
                or len(sentence_buffer) > 100
            ):
                print(f"buffer: {sentence_buffer}")
                continue

            start = time.perf_counter()

            chinese_text = translator.translate(sentence_buffer)

            cost = time.perf_counter() - start

            print(f"[Translator] {cost:.2f}s")

            chinese_queue.put((sentence_buffer, chinese_text))

            # 清空已翻譯內容
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
