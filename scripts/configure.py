#!/usr/bin/env python3
"""Create a private first-run Compose .env without printing secrets or overwriting files."""

import getpass
import json
import os
import re
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_config(path: Path, token: str, admin_ids: list[int]):
    if not re.fullmatch(r"[0-9]{5,20}:[A-Za-z0-9_-]{20,}", token):
        raise ValueError("Invalid Telegram token format")
    if (
        not admin_ids
        or any(type(value) is not int or value <= 0 for value in admin_ids)
        or len(set(admin_ids)) != len(admin_ids)
    ):
        raise ValueError("Administrator IDs must be positive and unique")
    password = secrets.token_urlsafe(24)
    replacements = {
        "BOT_TOKEN": token,
        "ADMIN_IDS": json.dumps(admin_ids),
        "POSTGRES_PASSWORD": password,
        "DATABASE_URL": f"postgresql+asyncpg://services:{password}@postgres:5432/services",
    }
    lines = []
    for line in (ROOT / ".env.example").read_text().splitlines():
        name = line.split("=", 1)[0]
        lines.append(f"{name}={replacements[name]}" if name in replacements else line)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as file:
        file.write("\n".join(lines) + "\n")


def main():
    path = ROOT / ".env"
    if path.exists():
        raise SystemExit(".env already exists; edit it privately instead of overwriting it.")
    token = getpass.getpass("Telegram bot token (hidden): ").strip()
    raw = input("Administrator user IDs, separated by commas: ")
    try:
        try:
            admins = [int(value.strip()) for value in raw.split(",")]
        except ValueError:
            raise ValueError("Invalid administrator IDs") from None
        write_config(path, token, admins)
    except (ValueError, OSError) as error:
        if isinstance(error, ValueError):
            raise SystemExit(str(error)) from None
        raise SystemExit(
            "Could not create private .env; existing files were not overwritten."
        ) from None
    print("Created private .env for Docker Compose. AI remains disabled until configured.")


if __name__ == "__main__":
    main()
