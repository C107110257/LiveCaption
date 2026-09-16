import threading
import warnings
import os
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_XET"] = "1"

from soundcard.mediafoundation import SoundcardRuntimeWarning
warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)

from audio.recorder import AudioRecorder
from ui.caption_window import CaptionWindow
from config.settings import *

from pipeline.state import (
    audio_queue,
    translator_ready_event,
    whisper_ready_event,
)
from pipeline.whisper_worker import transcribe_loop
from pipeline.translator_worker import load_translator, translate_loop
from pipeline.ui_worker import ui_loop

caption_window = CaptionWindow()


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


def on_audio_status_change(is_ready: bool, message: str):
    """
    錄音裝置狀態改變時的回呼(初始化失敗 或 錄音中途中斷 都會呼叫這裡)
    """
    if not is_ready:
        caption_window.update_text(
            "音訊裝置異常",
            message or "找不到可用的音訊裝置，請確認輸出裝置設定",
            "#FF4444",
        )


def startup():

    print_startup_config()

    # AudioRecorder 移到這裡建立,並掛上狀態回呼
    recorder = AudioRecorder(audio_queue, status_callback=on_audio_status_change)

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

    if not recorder.device_ready:
        # 不啟動 Recorder 執行緒,也不顯示 ready
        # on_audio_status_change 在建立 AudioRecorder 當下就已經顯示過錯誤訊息了
        return

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