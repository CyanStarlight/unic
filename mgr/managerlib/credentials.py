from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import keyring
from keyring.errors import KeyringError
import requests

from .config import (
    ConfigError,
    ConfigManager,
    DEFAULT_CONFIG_DIR,
    DEFAULT_PASSWORD_REF,
    DEFAULT_PRIVATE_TOKEN_REF,
    DEFAULT_TOKEN_REF,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_SERVICE_ID = "moodle_mobile_app"
DEFAULT_SECRET_FILE = DEFAULT_CONFIG_DIR / "secrets.json"
REQUEST_TIMEOUT = 30


class CredentialError(ConfigError):
    """Raised when Moodle credentials are missing or invalid."""


class _SecretBackend:
    """Stores secrets in the system keyring with a file-based fallback."""

    def __init__(self, service_name: str, fallback_path: Path = DEFAULT_SECRET_FILE) -> None:
        self.service_name = service_name
        self.fallback_path = fallback_path

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def get(self, name: str) -> Optional[str]:
        value = self._get_from_keyring(name)
        if value is not None:
            return value
        return self._get_from_file().get(name)

    def set(self, name: str, value: str) -> None:
        stored = self._set_in_keyring(name, value)
        if not stored:
            data = self._get_from_file()
            data[name] = value
            self._write_to_file(data)

    def delete(self, name: str) -> None:
        deleted = self._delete_from_keyring(name)
        data = self._get_from_file()
        if name in data:
            data.pop(name)
            self._write_to_file(data)
        if not deleted and name not in data:
            # nothing to do
            return

    # ------------------------------------------------------------------
    # Keyring interaction
    # ------------------------------------------------------------------
    def _get_from_keyring(self, name: str) -> Optional[str]:
        try:
            return keyring.get_password(self.service_name, name)
        except KeyringError:
            LOGGER.debug("Keyring backend unavailable for %s", name)
            return None

    def _set_in_keyring(self, name: str, value: str) -> bool:
        try:
            keyring.set_password(self.service_name, name, value)
            return True
        except KeyringError:
            LOGGER.debug("Unable to store %s in system keyring", name)
            return False

    def _delete_from_keyring(self, name: str) -> bool:
        try:
            keyring.delete_password(self.service_name, name)
            return True
        except KeyringError:
            return False

    # ------------------------------------------------------------------
    # File fallback
    # ------------------------------------------------------------------
    def _get_from_file(self) -> Dict[str, str]:
        if not self.fallback_path.exists():
            return {}
        try:
            with open(self.fallback_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            LOGGER.warning("Secret fallback file is corrupted; recreating it.")
            return {}

    def _write_to_file(self, data: Dict[str, str]) -> None:
        self.fallback_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.fallback_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        os.replace(tmp_path, self.fallback_path)
        try:
            os.chmod(self.fallback_path, 0o600)
        except OSError:
            LOGGER.debug("Unable to set permissions on %s", self.fallback_path)


class MoodleCredentialStore:
    """Handles Moodle tokens and automatic refresh using stored secrets."""

    def __init__(
        self,
        config: ConfigManager,
        *,
        service_name: str = "unic-manager",
        session: Optional[requests.Session] = None,
        service_id: str = DEFAULT_SERVICE_ID,
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.service_id = service_id
        self.backend = _SecretBackend(service_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_token(self, *, ensure_fresh: bool = True) -> str:
        metadata = self.config.effective_moodle_config()
        token = self._resolve_token(metadata)
        if not token and ensure_fresh:
            return self.refresh_token(metadata)
        if not token:
            raise CredentialError(
                "No Moodle token found. Use the configuration menu to store one "
                "or set UNIC_MOODLE_TOKEN."
            )

        if ensure_fresh and self._should_refresh(metadata):
            try:
                return self.refresh_token(metadata)
            except CredentialError as exc:
                LOGGER.warning("Token refresh failed, continuing with cached token: %s", exc)
        return token

    def refresh_token(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        metadata = metadata or self.config.effective_moodle_config()
        base_url = self.config.require_moodle_base_url()

        payload_base: Dict[str, str] = {"service": self.service_id}
        attempts = self._build_refresh_attempts(metadata)
        if not attempts:
            raise CredentialError(
                "Unable to refresh token automatically. Store either a Moodle "
                "password or the private token via the configuration menu."
            )

        last_error: Optional[str] = None
        for attempt in attempts:
            method, payload = attempt
            response = self.session.post(
                f"{base_url}/login/token.php",
                data={**payload_base, **payload},
                timeout=REQUEST_TIMEOUT,
            )
            result, error = self._handle_response(response)
            if result:
                token = result["token"]
                private_token = result.get("privatetoken")
                self._persist_tokens(metadata, token, private_token)
                self.config.mark_token_acquired()
                self.config.record_refresh_attempt(success=True)
                return token
            last_error = error

        # If we reach here, every attempt failed.
        self.config.record_refresh_attempt(success=False, error_message=last_error)
        raise CredentialError(last_error or "Failed to obtain Moodle token")

    def store_credentials(
        self,
        *,
        token: Optional[str] = None,
        private_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        metadata = self.config.get_moodle_config()
        token_ref = metadata.get("token_ref", DEFAULT_TOKEN_REF)
        private_ref = metadata.get("private_ref", DEFAULT_PRIVATE_TOKEN_REF)
        password_ref = metadata.get("password_ref", DEFAULT_PASSWORD_REF)

        if token is not None:
            cleaned_token = token.strip()
            if cleaned_token:
                self.backend.set(token_ref, cleaned_token)
                # keep legacy field empty to avoid storing plaintext
                self.config.update_moodle_config(token="")
                self.config.mark_token_acquired()
            else:
                self.backend.delete(token_ref)
                self.config.update_moodle_config(token="")

        if private_token:
            self.backend.set(private_ref, private_token.strip())
        else:
            self.backend.delete(private_ref)

        if password:
            self.backend.set(password_ref, password)
        elif password is not None:
            self.backend.delete(password_ref)

        if username is not None:
            self.config.update_moodle_config(username=username.strip())

    def clear_credentials(self) -> None:
        metadata = self.config.get_moodle_config()
        self.backend.delete(metadata.get("token_ref", DEFAULT_TOKEN_REF))
        self.backend.delete(metadata.get("private_ref", DEFAULT_PRIVATE_TOKEN_REF))
        self.backend.delete(metadata.get("password_ref", DEFAULT_PASSWORD_REF))
        self.config.update_moodle_config(token="", username="")

    def has_private_token(self) -> bool:
        return self._resolve_private_token(self.config.get_moodle_config()) is not None

    def has_stored_password(self) -> bool:
        return self._resolve_password(self.config.get_moodle_config()) is not None

    def has_token(self) -> bool:
        return self._resolve_token(self.config.get_moodle_config()) is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_token(self, metadata: Dict[str, Any]) -> Optional[str]:
        env_token = os.getenv("UNIC_MOODLE_TOKEN")
        if env_token:
            return env_token.strip()
        legacy = metadata.get("token")
        if legacy:
            return legacy.strip()
        token_ref = metadata.get("token_ref", DEFAULT_TOKEN_REF)
        return self.backend.get(token_ref)

    def _resolve_private_token(self, metadata: Dict[str, Any]) -> Optional[str]:
        env_private = os.getenv("UNIC_MOODLE_PRIVATETOKEN")
        if env_private:
            return env_private.strip()
        private_ref = metadata.get("private_ref", DEFAULT_PRIVATE_TOKEN_REF)
        return self.backend.get(private_ref)

    def _resolve_password(self, metadata: Dict[str, Any]) -> Optional[str]:
        env_password = os.getenv("UNIC_MOODLE_PASSWORD")
        if env_password:
            return env_password
        password_ref = metadata.get("password_ref", DEFAULT_PASSWORD_REF)
        return self.backend.get(password_ref)

    def _resolve_username(self, metadata: Dict[str, Any]) -> Optional[str]:
        username = metadata.get("username")
        env_username = os.getenv("UNIC_MOODLE_USERNAME")
        if env_username:
            return env_username.strip()
        return username.strip() if isinstance(username, str) and username.strip() else None

    def _should_refresh(self, metadata: Dict[str, Any]) -> bool:
        ttl = metadata.get("token_ttl_hours")
        acquired = metadata.get("last_token_acquired")
        if not ttl or ttl <= 0 or not acquired:
            return False
        timestamp = self._parse_iso(acquired)
        if not timestamp:
            return False
        return datetime.now(timezone.utc) - timestamp >= timedelta(hours=int(ttl))

    def _build_refresh_attempts(self, metadata: Dict[str, Any]) -> list[tuple[str, Dict[str, str]]]:
        attempts: list[tuple[str, Dict[str, str]]] = []
        private_token = self._resolve_private_token(metadata)
        if private_token:
            attempts.append(("privatetoken", {"privatetoken": private_token}))
            # some Moodle setups expect the parameter name "token"
            attempts.append(("token", {"token": private_token, "refresh": "1"}))
        username = self._resolve_username(metadata)
        password = self._resolve_password(metadata)
        if username and password:
            attempts.append(("credentials", {"username": username, "password": password}))
        return attempts

    def _handle_response(
        self, response: requests.Response
    ) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, json.JSONDecodeError) as exc:
            LOGGER.debug("Error during token refresh: %s", exc)
            return None, str(exc)

        if isinstance(data, dict) and "token" in data:
            return data, None
        if isinstance(data, dict) and data.get("error"):
            error_msg = str(data.get("error"))
            LOGGER.debug("Token refresh attempt failed: %s", error_msg)
            return None, error_msg
        return None, "Unexpected response from Moodle token endpoint"

    def _persist_tokens(
        self,
        metadata: Dict[str, Any],
        token: str,
        private_token: Optional[str],
    ) -> None:
        token_ref = metadata.get("token_ref", DEFAULT_TOKEN_REF)
        private_ref = metadata.get("private_ref", DEFAULT_PRIVATE_TOKEN_REF)
        self.backend.set(token_ref, token)
        if private_token:
            self.backend.set(private_ref, private_token)
        else:
            self.backend.delete(private_ref)
        self.config.update_moodle_config(token="")

    @staticmethod
    def _parse_iso(value: str) -> Optional[datetime]:
        try:
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except ValueError:
            return None