from pathlib import Path
from typing import Optional, Sequence
import os

# 必須在 import huggingface_hub 之前設定，Xet backend 才會照這個設定初始化。
# Xet 傳輸會用背景 Rust thread 自己畫進度條，不受 Python 這邊的 tqdm_class 控制，
# 停用後全部改用一般 HTTP 下載，進度才能交給我們自己的 BarTqdm 畫。
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

from huggingface_hub import snapshot_download
from huggingface_hub.utils import HfHubHTTPError

from .progress import BarTqdm


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
    - 進度條改用 progress.py 的 BarTqdm，樣式跟 shared_storage_source 一致。
      註：huggingface_hub 的 tqdm_class 只控制「整個 repo 抓取幾個檔案」這一層的
      彙總進度，單一大檔案內部的位元組級進度條目前版本不一定會套用同一個
      class（官方文件也註明這點）。如果之後版本行為不同、畫面又變亂，
      最保險的退路是把 tqdm_class 拿掉、改回 HF_HUB_DISABLE_PROGRESS_BARS=1
      完全關閉，只看我們自己印的 [Startup] 訊息。
    """
    print(f"[Startup] Downloading from {repo_id} (allow_patterns={list(allow_patterns) if allow_patterns else 'ALL FILES'})")
    try:
        snapshot_download(
            repo_id=repo_id,
            revision=revision,
            local_dir=str(local_path),
            token=token,
            allow_patterns=list(allow_patterns) if allow_patterns else None,
            tqdm_class=BarTqdm,
        )
    except HfHubHTTPError as e:
        raise RuntimeError(f"Hugging Face download failed for {repo_id}: {e}") from e