from ui.console import ConsoleUI
from pipeline.state import chinese_queue


def ui_loop(caption_window):

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