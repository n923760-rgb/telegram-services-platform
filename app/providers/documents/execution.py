"""Shared per-worker native capacity and subprocess cleanup (not a sandbox)."""

import asyncio
import os
import signal
import sys
from weakref import WeakKeyDictionary

from app.providers.documents.base import DocumentError

_slots = WeakKeyDictionary()


def slot():
    loop = asyncio.get_running_loop()
    if loop not in _slots:
        _slots[loop] = asyncio.Semaphore(1)
    return _slots[loop]


async def stop(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    await process.wait()


async def run_child(module, args, *, timeout, unavailable_key, timeout_key):
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            module,
            *args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        raise DocumentError(unavailable_key) from None
    try:
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout)
        except TimeoutError:
            raise DocumentError(timeout_key) from None
        if process.returncode != 0:
            raise DocumentError(unavailable_key)
    finally:
        # Reap the launcher and terminate any remaining children before file cleanup.
        await stop(process)
