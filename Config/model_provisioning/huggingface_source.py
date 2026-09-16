from pathlib import Path
from typing import Optional, Sequence

from huggingface_hub import snapshot_download
from huggingface_hub.utils import HfHubHTTPError


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
    - 下載進度由 huggingface_hub 內建的 tqdm 進度條顯示，不需要額外處理。
    """
    print(f"[Startup] Downloading from {repo_id} (allow_patterns={list(allow_patterns) if allow_patterns else 'ALL FILES'})")
    try:
        snapshot_download(
            repo_id=repo_id,
            revision=revision,
            local_dir=str(local_path),
            token=token,
            allow_patterns=list(allow_patterns) if allow_patterns else None,
        )
    except HfHubHTTPError as e:
        raise RuntimeError(f"Hugging Face download failed for {repo_id}: {e}") from e