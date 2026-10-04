import json
import stat

import pytest

from scripts.configure import write_config


def test_configuration_is_private_consistent_and_never_overwrites(tmp_path):
    target = tmp_path / ".env"
    token = "123456:" + "A" * 35
    write_config(target, token, [123456])
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    values = dict(
        line.split("=", 1)
        for line in target.read_text().splitlines()
        if "=" in line and not line.startswith("#")
    )
    assert values["BOT_TOKEN"] == token
    assert json.loads(values["ADMIN_IDS"]) == [123456]
    assert values["POSTGRES_PASSWORD"] in values["DATABASE_URL"]
    assert values["AI_ENABLED"] == "false"
    content = target.read_bytes()
    with pytest.raises(FileExistsError):
        write_config(target, token, [987654])
    assert target.read_bytes() == content


def test_configuration_rejects_environment_injection(tmp_path):
    with pytest.raises(ValueError):
        write_config(tmp_path / ".env", "123456:token\nADMIN_IDS=[999]", [123])
    assert not (tmp_path / ".env").exists()
