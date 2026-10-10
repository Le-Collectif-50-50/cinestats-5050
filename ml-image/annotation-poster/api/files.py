"""Écritures atomiques et empreintes des fichiers d’annotation."""
import hashlib
import json
import os
import tempfile
from pathlib import Path


def atomic_json(path: Path, value):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.write-')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
