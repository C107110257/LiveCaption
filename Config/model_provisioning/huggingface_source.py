from pathlib import Path
from typing import Optional, Sequence
import os

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

from huggingface_hub import snapshot_download
from huggingface_hub.utils import HfHubHTTPError, disable_progress_bars

disable_progress_bars()

def fetch_from_huggingface(
    repo_id: str,
    local_path: Path,
    revision: str = "main",
    token: Optional[str] = None,
    allow_patterns: Optional[Sequence[str]] = None,
) -> None:
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