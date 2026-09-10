import threading
import warnings
from soundcard.mediafoundation import SoundcardRuntimeWarning
warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)

from audio.recorder import AudioRecorder
from ui.caption_window import CaptionWindow
from Config.Config import *

from pipeline.state import (
    audio_queue,
    translator_ready_event,
    whisper_ready_event,
)
from pipeline.whisper_worker import transcribe_loop
from pipeline.translator_worker import load_translator, translate_loop
from pipeline.ui_worker import ui_loop

caption_window = CaptionWindow()
recorder = AudioRecorder(audio_queue)


def print_startup_config():
    print("=" * 50)
    print("  Live Caption - 啟動設定")
    print("=" * 50)
    print(f"  Whisper Model     : {whisper_model}")
    print(f"  Translate Model   : {translate_model}")
    print(f"  Translate CT2     : {translate_model_ct2}")
    print(f"  Window / Step (s) : {WINDOW_SECONDS} / {STEP_SECONDS}")
    print(f"  Beam Size         : {BEAM_SIZE}")
    print(f"  Whisper Threads   : {WHISPER_CPU_THREADS}")
    print(f"  Translator Threads: {TRANSLATOR_INTRA_THREADS}")
    print("=" * 50)


def startup():

    print_startup_config()

    

    threading.Thread(
        name="TranslatorLoader",
        target=load_translator,
        args=(caption_window.update_text,),
        daemon=True,
    ).start()

    threading.Thread(
        name="Whisper",
        target=transcribe_loop,
        args=(caption_window.update_text,),
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
        args=(caption_window,),
        daemon=True,
    ).start()

    translator_ready_event.wait()
    whisper_ready_event.wait()
    
    threading.Thread(
            name="Recorder",
            target=recorder.run,
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