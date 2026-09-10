import time

from speech.transcriber import AudioTranscriber
from pipeline.state import audio_queue, english_queue, whisper_ready_event


def transcribe_loop(status_callback):

    transcriber = AudioTranscriber(status_callback=status_callback)

    whisper_ready_event.set()

    while True:

        audio = audio_queue.get()

        try:
            start = time.perf_counter()
            text = transcriber.transcribe(audio)
            cost = time.perf_counter() - start

            print(f"[Whisper] {cost:.2f}s")

            english_queue.put(text)

        except Exception as ex:
            print(f"[Whisper] {ex}")

        finally:
            audio_queue.task_done()