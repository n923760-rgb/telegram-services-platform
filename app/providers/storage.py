import fcntl
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
    def expire_before(self, cutoff, keep: set[str] | None = None): ...


class LocalStorage(Storage):
    def __init__(self, root: Path, max_bytes=10485760, quota_bytes=52428800, quota_files=100):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.quota_bytes = quota_bytes
        self.quota_files = quota_files

    def path(self, key, user_id=None):
        if not re.fullmatch(r"[0-9]+/[a-f0-9]{32}/[a-zA-Z0-9_.-]+", key):
            raise ServiceError("file_invalid")
        if user_id is not None and key.split("/")[0] != str(user_id):
            raise ServiceError("not_allowed")
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ServiceError("not_allowed")
        return path

    def expire_before(self, cutoff, keep=None):
        # Keep operational locks; expire only customer file namespaces. Keys in
        # `keep` are preserved so age expiry never destroys live order files or
        # retry references for terminal orders whose deletion is still pending.
        keep = keep or set()
        for path in self.root.glob("[0-9]*/*/*"):
            if not path.is_file() or datetime.fromtimestamp(path.stat().st_mtime, UTC) >= cutoff:
                continue
            if path.relative_to(self.root).as_posix() in keep:
                continue
            path.unlink(missing_ok=True)
            try:
                path.parent.rmdir()
            except OSError:
                pass

    def _owner_dir(self, user_id):
        return self.root / str(user_id)

    def _lock_path(self, user_id):
        return self.root / f".quota-{user_id}.lock"

    def usage(self, user_id):
        """Return (total_bytes, file_count) currently stored for the owner."""
        owner = self._owner_dir(user_id)
        if not owner.is_dir():
            return 0, 0
        total, count = 0, 0
        for path in owner.glob("*/*"):
            if path.is_file():
                total += path.stat().st_size
                count += 1
        return total, count

    def _check_quota_locked(self, user_id, incoming_bytes, incoming_files):
        total, count = self.usage(user_id)
        if total + incoming_bytes > self.quota_bytes or count + incoming_files > self.quota_files:
            raise ServiceError("storage_quota")

    def ensure_quota(self, user_id, incoming_bytes=0, incoming_files=1):
        """Advisory pre-check (before an expensive download) that raises ``storage_quota``
        if the owner would exceed their per-owner byte/file quota. The authoritative check
        still runs inside :meth:`save` under the same lock as the write."""
        with self._lock_path(user_id).open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self._check_quota_locked(user_id, incoming_bytes, incoming_files)

    def save(self, user_id, filename, data, mime):
        if not data or len(data) > self.max_bytes or user_id <= 0:
            raise ServiceError("file_invalid")
        filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(filename).name)[:100]
        if not filename or filename.startswith("."):
            raise ServiceError("file_invalid")
        key = f"{user_id}/{uuid4().hex}/{filename}"
        path = self.path(key, user_id)
        temporary = path.with_suffix(path.suffix + ".tmp")
        # Enforce the per-owner quota under a POSIX lock so concurrent bot/worker uploads
        # cannot overshoot it between the check and the write. Create the destination
        # directory only after the authoritative quota check so a rejected save never
        # leaves an empty UUID directory behind.
        with self._lock_path(user_id).open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self._check_quota_locked(user_id, len(data), 1)
            path.parent.mkdir(parents=True, exist_ok=True)
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
