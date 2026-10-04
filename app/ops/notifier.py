import fcntl
import time
from uuid import uuid4

from app.core.i18n import tr
from app.core.settings import config


class Notifier:
    def __init__(self, redis, channel):
        self.redis, self.channel = redis, channel

    async def alert(self, kind, **context):
        # Store a claim token, never secrets or customer inputs.
        scope = context.get("slug", "global")
        key = f"alert:{kind}:global"
        token = uuid4().hex
        fallback = None
        try:
            allowed = await self.redis.set(key, token, nx=True, ex=900)
        except Exception:
            folder = config().storage_root / "ops"
            folder.mkdir(parents=True, exist_ok=True)
            fallback = folder / (key.replace(":", "_") + ".lock")
            with fallback.open("a+") as file:
                fcntl.flock(file, fcntl.LOCK_EX)
                file.seek(0)
                last = float(file.read() or "0")
                allowed = time.time() - last >= 900
                if allowed:
                    stamp = time.time()
                    file.seek(0)
                    file.truncate()
                    file.write(str(stamp))
        if not allowed:
            return False
        try:
            await self.channel.send("alert", kind=tr("alert_" + kind), slug=scope)
        except Exception:
            if fallback:
                with fallback.open("a+") as file:
                    fcntl.flock(file, fcntl.LOCK_EX)
                    file.seek(0)
                    if float(file.read() or "0") == stamp:
                        file.seek(0)
                        file.truncate()
                        file.write("0")
            else:
                try:
                    await self.redis.eval(
                        "if redis.call('GET',KEYS[1])==ARGV[1] then return redis.call('DEL',KEYS[1]) end return 0",
                        1,
                        key,
                        token,
                    )
                except Exception:
                    pass  # The claim still expires; no permanent suppression.
            raise
        return True
