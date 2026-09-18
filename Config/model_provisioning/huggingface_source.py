from pathlib import Path
from typing import Optional, Sequence
import fnmatch
import threading
import time

from huggingface_hub import HfApi, snapshot_download
from huggingface_hub.utils import HfHubHTTPError

from .progress import ProgressReporter
from .shared_storage_source import get_dir_size

# huggingface_hub 目前版本的 Xet 雙進度條是寫死接在 snapshot_download 內部的，
# 不吃 tqdm_class、也不能靠解除安裝/排除模組關掉（見 fetch_from_huggingface
# 的說明），所以這裡直接關掉內建顯示，改成自己輪詢資料夾大小畫進度條。
import os
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
from huggingface_hub.utils import disable_progress_bars
disable_progress_bars()

POLL_INTERVAL_SECONDS = 0.5


def _estimate_total_size(
    repo_id: str,
    revision: str,
    allow_patterns: Optional[Sequence[str]],
) -> int:
    """問 Hugging Face 這次要抓的檔案總共多大（bytes），抓不到就回傳 0（代表不顯示進度條）"""
    api = HfApi()
    info = api.model_info(repo_id, revision=revision, files_metadata=True)

    total = 0
    for sibling in info.siblings:
        if sibling.size is None:
            continue
        if allow_patterns and not any(
            fnmatch.fnmatch(sibling.rfilename, pattern) for pattern in allow_patterns
        ):
            continue
        total += sibling.size

    return total


def fetch_from_huggingface(
    repo_id: str,
    local_path: Path,
    revision: str = "main",
    token: Optional[str] = None,
    allow_patterns: Optional[Sequence[str]] = None,
) -> None:
    """
    從 Hugging Face Hub 下載模型到本機。
    - repo_id: 例如 "facebook/nllb-200-distilled-1.3B"
    - token: 若模型為 private，需要有權限的 token；
      未提供時會嘗試使用 `hf auth login` 已快取的登入 token。
    - allow_patterns: 只下載這些檔名，避免把整個 repo（可能包含用不到的權重檔）都抓下來。
      未提供時會下載整個 repo。
    - 進度條：huggingface_hub 內建的進度顯示已關閉（見上方說明），改成自己在
      背景 thread 跑 snapshot_download，主執行緒輪詢資料夾大小算進度，畫面
      跟 shared_storage_source 一致。
    """
    print(f"[Startup] Downloading from {repo_id} (allow_patterns={list(allow_patterns) if allow_patterns else 'ALL FILES'})")

    try:
        total_size = _estimate_total_size(repo_id, revision, allow_patterns)
    except Exception as e:
        print(f"[Startup] Could not estimate total size ({e}), progress bar disabled")
        total_size = 0

    local_path.mkdir(parents=True, exist_ok=True)

    result = {}

    def _run_download():
        try:
            snapshot_download(
                repo_id=repo_id,
                revision=revision,
                local_dir=str(local_path),
                token=token,
                allow_patterns=list(allow_patterns) if allow_patterns else None,
            )
        except Exception as e:
            result["error"] = e

    download_thread = threading.Thread(target=_run_download, daemon=True)
    download_thread.start()

    if total_size > 0:
        reporter = ProgressReporter(total_size)
        last_copied = 0

        while download_thread.is_alive():
            time.sleep(POLL_INTERVAL_SECONDS)
            current = min(get_dir_size(local_path), total_size)
            if current > last_copied:
                reporter.update(current - last_copied)
                last_copied = current

        download_thread.join()

        final_size = min(get_dir_size(local_path), total_size)
        if final_size > last_copied:
            reporter.update(final_size - last_copied)
        reporter.close()
    else:
        download_thread.join()

    if "error" in result:
        raise RuntimeError(f"Hugging Face download failed for {repo_id}: {result['error']}") from result["error"]