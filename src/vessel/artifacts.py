import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel

SENSITIVE = re.compile(r"api[-_]?key|authorization|password|secret|access[-_]?token|cookie", re.I)


def sanitize(value, secrets: tuple[str, ...] = ()):
    if isinstance(value, dict):
        return {
            k: "[REDACTED]" if SENSITIVE.search(k) else sanitize(v, secrets)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [sanitize(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        if value.startswith(("http://", "https://")):
            p = urlsplit(value)
            if p.username or p.password:
                value = "[REDACTED URL]"
            else:
                pairs = [
                    (k, "[REDACTED]" if SENSITIVE.search(k) else v)
                    for k, v in parse_qsl(p.query, keep_blank_values=True)
                ]
                value = urlunsplit((p.scheme, p.netloc, p.path, urlencode(pairs), p.fragment))
        return value
    return value


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, content: bytes) -> str:
        sha = hashlib.sha256(content).hexdigest()
        path = self.root / sha[:2] / sha
        path.parent.mkdir(exist_ok=True)
        if not path.exists():
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(content)
            tmp.replace(path)
        return sha

    def read(self, sha: str) -> bytes:
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("invalid artifact digest")
        content = (self.root / sha[:2] / sha).read_bytes()
        if hashlib.sha256(content).hexdigest() != sha:
            raise ValueError("artifact integrity mismatch")
        return content
