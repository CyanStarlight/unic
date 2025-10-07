from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = ["ConfigManager", "ConfigError", "MoodleConfig"]

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "unic-manager"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"
CONFIG_PATH_ENV = "UNIC_MANAGER_CONFIG_PATH"

DEFAULT_TOKEN_REF = "moodle-token"
DEFAULT_PRIVATE_TOKEN_REF = "moodle-private-token"
DEFAULT_PASSWORD_REF = "moodle-password"
DEFAULT_TOKEN_TTL_HOURS = 720  # 30 days

MoodleConfig = Dict[str, Any]


class ConfigError(RuntimeError):
    """Raised when configuration data is missing or malformed."""


@dataclass
class ConfigManager:
    """Small helper that persists manager configuration as JSON."""

    path: Path | str | None = None
    _data: Dict[str, Any] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        resolved = self._resolve_path(self.path)
        self.path = resolved
        self._data = {}
        self._load()

    @staticmethod
    def _resolve_path(path: Path | str | None) -> Path:
        if path:
            return Path(path).expanduser()
        env_path = os.getenv(CONFIG_PATH_ENV)
        if env_path:
            return Path(env_path).expanduser()
        return DEFAULT_CONFIG_PATH

    # ------------------------------------------------------------------
    # Basic file operations
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if Path(self.path).exists():
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    self._data = json.load(fh)
            except json.JSONDecodeError as exc:
                raise ConfigError(
                    f"Configuration file at {self.path} is not valid JSON"
                ) from exc
        else:
            self._data = {"moodle": self._default_moodle_config()}

    def save(self) -> None:
        path_obj = Path(self.path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(path_obj, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    # ------------------------------------------------------------------
    # Moodle configuration helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _default_moodle_config() -> MoodleConfig:
        return {
            "base_url": "",
            "download_files": False,
            "max_file_size": 25 * 1024 * 1024,  # 25 MiB
            "token": "",  # legacy storage for backwards compatibility
            "token_ref": DEFAULT_TOKEN_REF,
            "private_ref": DEFAULT_PRIVATE_TOKEN_REF,
            "username": "",
            "password_ref": DEFAULT_PASSWORD_REF,
            "last_token_acquired": None,
            "last_refresh_attempt": None,
            "last_refresh_error": "",
            "token_ttl_hours": DEFAULT_TOKEN_TTL_HOURS,
        }

    def get_moodle_config(self) -> MoodleConfig:
        moodle = self._data.setdefault("moodle", self._default_moodle_config())
        return {
            "base_url": moodle.get("base_url", ""),
            "token": moodle.get("token", ""),
            "download_files": bool(moodle.get("download_files", False)),
            "max_file_size": moodle.get("max_file_size"),
            "token_ref": moodle.get("token_ref", DEFAULT_TOKEN_REF),
            "private_ref": moodle.get("private_ref", DEFAULT_PRIVATE_TOKEN_REF),
            "username": moodle.get("username", ""),
            "password_ref": moodle.get("password_ref", DEFAULT_PASSWORD_REF),
            "last_token_acquired": moodle.get("last_token_acquired"),
            "last_refresh_attempt": moodle.get("last_refresh_attempt"),
            "last_refresh_error": moodle.get("last_refresh_error", ""),
            "token_ttl_hours": moodle.get("token_ttl_hours", DEFAULT_TOKEN_TTL_HOURS),
        }

    def effective_moodle_config(self) -> MoodleConfig:
        config = self.get_moodle_config()

        base_url_override = os.getenv("UNIC_MOODLE_BASE_URL")
        token_override = os.getenv("UNIC_MOODLE_TOKEN")
        download_override = os.getenv("UNIC_MOODLE_DOWNLOAD_FILES")
        size_override = os.getenv("UNIC_MOODLE_MAX_FILE_SIZE")
        ttl_override = os.getenv("UNIC_MOODLE_TOKEN_TTL_HOURS")

        if base_url_override:
            config["base_url"] = base_url_override.strip()
        if token_override:
            config["token"] = token_override.strip()
        if download_override:
            config["download_files"] = download_override.strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        if size_override:
            try:
                config["max_file_size"] = int(size_override)
            except ValueError as exc:
                raise ConfigError(
                    "UNIC_MOODLE_MAX_FILE_SIZE must be an integer representing bytes"
                ) from exc
        if ttl_override:
            try:
                config["token_ttl_hours"] = int(ttl_override)
            except ValueError as exc:
                raise ConfigError(
                    "UNIC_MOODLE_TOKEN_TTL_HOURS must be an integer"
                ) from exc

        return config

    def update_moodle_config(
        self,
        *,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        download_files: Optional[bool] = None,
        max_file_size: Optional[int] = None,
        token_ref: Optional[str] = None,
        private_ref: Optional[str] = None,
    username: Optional[str] = None,
        password_ref: Optional[str] = None,
        token_ttl_hours: Optional[int] = None,
        last_token_acquired: Optional[str] = None,
        last_refresh_attempt: Optional[str] = None,
        last_refresh_error: Optional[str] = None,
    ) -> MoodleConfig:
        moodle = self._data.setdefault("moodle", self._default_moodle_config())

        if base_url is not None:
            moodle["base_url"] = base_url.strip()
        if token is not None:
            moodle["token"] = token.strip()
        if download_files is not None:
            moodle["download_files"] = bool(download_files)
        if max_file_size is not None:
            if max_file_size <= 0:
                raise ConfigError("max_file_size must be a positive integer")
            moodle["max_file_size"] = int(max_file_size)
        if token_ref is not None:
            moodle["token_ref"] = token_ref.strip() or DEFAULT_TOKEN_REF
        if private_ref is not None:
            moodle["private_ref"] = private_ref.strip() or DEFAULT_PRIVATE_TOKEN_REF
        if username is not None:
            moodle["username"] = username.strip()
        if password_ref is not None:
            moodle["password_ref"] = password_ref.strip() or DEFAULT_PASSWORD_REF
        if token_ttl_hours is not None:
            if token_ttl_hours <= 0:
                raise ConfigError("token_ttl_hours must be a positive integer")
            moodle["token_ttl_hours"] = int(token_ttl_hours)
        if last_token_acquired is not None:
            moodle["last_token_acquired"] = last_token_acquired
        if last_refresh_attempt is not None:
            moodle["last_refresh_attempt"] = last_refresh_attempt
        if last_refresh_error is not None:
            moodle["last_refresh_error"] = last_refresh_error

        self.save()
        return self.get_moodle_config()

    def mark_token_acquired(self, timestamp: Optional[datetime] = None) -> None:
        iso_value = self._format_datetime(timestamp or datetime.now(timezone.utc))
        self.update_moodle_config(last_token_acquired=iso_value, last_refresh_error="")

    def record_refresh_attempt(
        self,
        *,
        success: bool,
        timestamp: Optional[datetime] = None,
        error_message: str | None = None,
    ) -> None:
        iso_value = self._format_datetime(timestamp or datetime.now(timezone.utc))
        self.update_moodle_config(
            last_refresh_attempt=iso_value,
            last_refresh_error="" if success else (error_message or ""),
        )

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def require_moodle_credentials(self) -> MoodleConfig:
        config = self.effective_moodle_config()
        base_url = config.get("base_url", "").strip()
        token = config.get("token", "").strip()

        env_token = os.getenv("UNIC_MOODLE_TOKEN")

        if not base_url:
            raise ConfigError(
                "Moodle base URL must be configured. Use the manager's configuration"
                " menu or set UNIC_MOODLE_BASE_URL."
            )

        if base_url.endswith("/"):
            config["base_url"] = base_url[:-1]

        if env_token:
            config["token"] = env_token.strip()
        elif token:
            config["token"] = token
        else:
            config["token"] = ""

        return config


    def require_moodle_base_url(self) -> str:
        base_url = self.effective_moodle_config().get("base_url", "").strip()
        if not base_url:
            raise ConfigError(
                "Moodle base URL must be configured. Use the manager's configuration"
                " menu or set UNIC_MOODLE_BASE_URL."
            )
        return base_url.rstrip("/")
