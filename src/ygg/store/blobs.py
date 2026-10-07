"""Content-addressed blob store: every raw byte string is written once, under its sha256."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path


class BlobStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, sha256: str, suffix: str = "") -> Path:
        return self.root / sha256[:2] / sha256[2:4] / f"{sha256}{suffix}"

    def has(self, sha256: str, suffix: str = "") -> bool:
        return self.path(sha256, suffix).exists()

    def put(self, data: bytes, suffix: str = "") -> str:
        """Write data if absent; return its sha256. Writes are atomic (temp file, then rename)."""
        digest = hashlib.sha256(data).hexdigest()
        dest = self.path(digest, suffix)
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(f".{dest.name}.{os.getpid()}.tmp")
            tmp.write_bytes(data)
            os.replace(tmp, dest)
        return digest

    def get(self, sha256: str, suffix: str = "") -> bytes:
        return self.path(sha256, suffix).read_bytes()
