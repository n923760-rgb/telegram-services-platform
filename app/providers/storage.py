import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.services.base import Artifact, ServiceError


class Storage(ABC):
    @abstractmethod
    def save(self, user_id: int, filename: str, data: bytes, mime: str) -> Artifact: ...
    @abstractmethod
    def read(self, key: str, user_id: int) -> bytes: ...
    @abstractmethod
    def delete(self, key: str, user_id: int): ...
    @abstractmethod
    def expire_before(self, cutoff): ...


class LocalStorage(Storage):
    def __init__(self, root: Path, max_bytes=10485760):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes

    def path(self, key, user_id=None):
        if not re.fullmatch(r"[0-9]+/[a-f0-9]{32}/[a-zA-Z0-9_.-]+", key):
            raise ServiceError("file_invalid")
        if user_id is not None and key.split("/")[0] != str(user_id):
            raise ServiceError("not_allowed")
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ServiceError("not_allowed")
        return path

    def expire_before(self, cutoff):
        # Keep operational locks; expire only customer file namespaces.
        for path in self.root.glob("[0-9]*/*/*"):
            if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime, UTC) < cutoff:
                path.unlink(missing_ok=True)
                try:
                    path.parent.rmdir()
                except OSError:
                    pass

    def save(self, user_id, filename, data, mime):
        if not data or len(data) > self.max_bytes or user_id <= 0:
            raise ServiceError("file_invalid")
        filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(filename).name)[:100]
        if not filename or filename.startswith("."):
            raise ServiceError("file_invalid")
        key = f"{user_id}/{uuid4().hex}/{filename}"
        path = self.path(key, user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(path)
        return Artifact(key=key, filename=filename, mime=mime)

    def read(self, key, user_id):
        path = self.path(key, user_id)
        if not path.is_file() or path.stat().st_size > self.max_bytes:
            raise ServiceError("file_expired")
        return path.read_bytes()

    def delete(self, key, user_id):
        path = self.path(key, user_id)
        path.unlink(missing_ok=True)
        try:
            path.parent.rmdir()
        except OSError:
            pass


class OwnedStorage:
    def __init__(self, storage, user_id):
        self.storage, self.user_id = storage, user_id

    def save(self, filename, data, mime):
        return self.storage.save(self.user_id, filename, data, mime)

    def read(self, key):
        return self.storage.read(key, self.user_id)

    def delete(self, key):
        return self.storage.delete(key, self.user_id)
