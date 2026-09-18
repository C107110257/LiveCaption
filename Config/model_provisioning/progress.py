import sys

try:
    from tqdm.auto import tqdm as _TqdmBase
except ImportError:  # tqdm 一定會隨 huggingface_hub 裝進來，這裡只是保險
    _TqdmBase = object


def format_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}TB"


def format_count(n: float) -> str:
    """給「檔案數」這種非位元組單位用，不換算 KB/MB，直接顯示整數"""
    return f"{int(n)}"


def print_progress(
    copied: int,
    total: int,
    bar_len: int = 30,
    prefix: str = "",
    value_formatter=format_size,
) -> None:
    """在同一行畫出 [####----] 樣式的進度條，用 \\r 覆蓋前一次輸出"""
    ratio = copied / total if total else 1
    ratio = min(ratio, 1.0)
    filled = int(bar_len * ratio)
    bar = "#" * filled + "-" * (bar_len - filled)
    percent = ratio * 100
    line = (
        f"  {prefix}[{bar}] {percent:5.1f}%  "
        f"{value_formatter(copied)}/{value_formatter(total)}"
    )
    sys.stdout.write("\r\033[K" + line)  # \033[K 清除從游標到行尾的所有字元
    sys.stdout.flush()


def finish_progress() -> None:
    """結束一段進度顯示，換行讓後續 log 不會接在同一行"""
    print()


class ProgressReporter:
    """
    封裝單一下載/複製任務的進度狀態，避免呼叫端自己維護 copied 變數。
    用法：
        reporter = ProgressReporter(total_bytes)
        reporter.update(n_bytes)   # 每讀寫一個 chunk 呼叫一次
        reporter.close()           # 完成後呼叫，換行收尾
    """

    def __init__(self, total: int, prefix: str = ""):
        self.total = total
        self.copied = 0
        self.prefix = prefix
        print_progress(0, total, prefix=prefix)

    def update(self, n_bytes: int) -> None:
        self.copied += n_bytes
        print_progress(self.copied, self.total, prefix=self.prefix)

    def close(self) -> None:
        finish_progress()


class BarTqdm(_TqdmBase):
    """
    給 huggingface_hub 的 snapshot_download(tqdm_class=...) 用的相容類別。
    介面上是一個 tqdm，但畫面改用 print_progress 的樣式，跟 240 備援來源一致。

    huggingface_hub 對「repo 裡有幾個檔案要抓」跟「單一檔案下載了幾個位元組」
    用的是同一個 tqdm 介面，但單位不同：前者 unit 是 "it"（純數量），
    後者 unit 是 "B"（位元組）。這裡依照 self.unit 決定要不要套用
    KB/MB/GB 的位元組格式化，避免把「5 個檔案」誤顯示成 "5.0B"。
    """

    def display(self, msg=None, pos=None):
        total = self.total or 0
        is_byte_unit = getattr(self, "unit", "it") in ("B", "iB", "bytes")
        formatter = format_size if is_byte_unit else format_count
        print_progress(
            self.n,
            total,
            prefix=(self.desc + " " if self.desc else ""),
            value_formatter=formatter,
        )

    def close(self):
        super().close()
        if not getattr(self, "leave", False):
            finish_progress()