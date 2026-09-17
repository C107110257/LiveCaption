from datetime import datetime
from pathlib import Path
import threading


class TranscriptLogger:
    """
    把每一組（英文, 中文）翻譯結果寫進 txt 檔。
    每次程式啟動會開一個新檔案（檔名帶啟動時間），持續寫入直到程式關閉。
    """

    def __init__(self, output_dir: Path, enabled: bool = True):
        self.enabled = enabled
        self._lock = threading.Lock()
        self._file = None
        self.path = None

        if not self.enabled:
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"transcript_{datetime.now():%Y%m%d_%H%M%S}.txt"
        self.path = output_dir / filename
        # line-buffered 不适用于二進位/多行寫入，這裡改成每次寫完手動 flush
        self._file = open(self.path, "a", encoding="utf-8")
        print(f"[Transcript] Logging to: {self.path}")

    def log(self, english_text: str, chinese_text: str) -> None:
        if not self.enabled or self._file is None:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")

        with self._lock:
            try:
                self._file.write(f"[{timestamp}] EN: {english_text}\n")
                self._file.write(f"          ZH: {chinese_text}\n\n")
                self._file.flush()
            except Exception as e:
                print(f"[Transcript] Write failed: {e}")

    def close(self) -> None:
        if self._file is not None:
            with self._lock:
                self._file.close()
                self._file = None