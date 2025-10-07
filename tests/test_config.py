from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from mgr.managerlib import config as config_module
from mgr.managerlib.config import ConfigError, ConfigManager


def test_config_defaults_when_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(path=config_path)

    moodle = manager.get_moodle_config()
    assert moodle["base_url"] == ""
    assert moodle["token"] == ""
    assert moodle["download_files"] is False
    assert moodle["token_ref"] == config_module.DEFAULT_TOKEN_REF
    assert moodle["private_ref"] == config_module.DEFAULT_PRIVATE_TOKEN_REF
    assert moodle["password_ref"] == config_module.DEFAULT_PASSWORD_REF
    assert moodle["token_ttl_hours"] == config_module.DEFAULT_TOKEN_TTL_HOURS


def test_update_and_reload_moodle_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(path=config_path)

    manager.update_moodle_config(
        base_url="https://moodle.example.com",
        token="abc123",
        download_files=True,
        max_file_size=1024,
        token_ttl_hours=12,
        username="student",
    )

    reloaded = ConfigManager(path=config_path)
    moodle = reloaded.get_moodle_config()
    assert moodle["base_url"] == "https://moodle.example.com"
    assert moodle["token"] == "abc123"
    assert moodle["download_files"] is True
    assert moodle["max_file_size"] == 1024
    assert moodle["token_ttl_hours"] == 12
    assert moodle["username"] == "student"


def test_env_overrides_take_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(path=config_path)
    manager.update_moodle_config(
        base_url="https://moodle.example.com",
        token="abc123",
    )

    monkeypatch.setenv("UNIC_MOODLE_BASE_URL", "https://override.example.com")
    monkeypatch.setenv("UNIC_MOODLE_TOKEN", "override-token")
    monkeypatch.setenv("UNIC_MOODLE_DOWNLOAD_FILES", "true")
    monkeypatch.setenv("UNIC_MOODLE_MAX_FILE_SIZE", "2048")
    monkeypatch.setenv("UNIC_MOODLE_TOKEN_TTL_HOURS", "36")

    effective = manager.effective_moodle_config()
    assert effective["base_url"] == "https://override.example.com"
    assert effective["token"] == "override-token"
    assert effective["download_files"] is True
    assert effective["max_file_size"] == 2048
    assert effective["token_ttl_hours"] == 36


def test_invalid_max_file_size_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(path=config_path)

    monkeypatch.setenv("UNIC_MOODLE_MAX_FILE_SIZE", "not-an-int")
    with pytest.raises(ConfigError):
        manager.effective_moodle_config()


def test_mark_token_acquired_records_timestamp(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(path=config_path)

    now = datetime(2025, 10, 7, 12, 0, tzinfo=timezone.utc)
    manager.mark_token_acquired(timestamp=now)

    moodle = manager.get_moodle_config()
    assert moodle["last_token_acquired"] == "2025-10-07T12:00:00Z"


def test_record_refresh_attempt_handles_error(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(path=config_path)

    now = datetime(2025, 10, 7, 13, 0, tzinfo=timezone.utc)
    manager.record_refresh_attempt(success=False, timestamp=now, error_message="boom")

    moodle = manager.get_moodle_config()
    assert moodle["last_refresh_attempt"] == "2025-10-07T13:00:00Z"
    assert moodle["last_refresh_error"] == "boom"
