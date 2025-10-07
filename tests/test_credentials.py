from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from mgr.managerlib.credentials import CredentialError, MoodleCredentialStore
from mgr.managerlib.config import ConfigManager


class MemoryBackend:
    def __init__(self) -> None:
        self.data: Dict[str, str] = {}

    def get(self, name: str) -> Optional[str]:
        return self.data.get(name)

    def set(self, name: str, value: str) -> None:
        self.data[name] = value

    def delete(self, name: str) -> None:
        self.data.pop(name, None)


class DummyResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:  # pragma: no cover - no-op
        return None

    def json(self) -> Dict[str, Any]:
        return self._payload


class DummySession:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[Dict[str, Any]] = []

    def post(self, url: str, data: Dict[str, Any], timeout: int) -> DummyResponse:  # pragma: no cover - simple harness
        self.calls.append({"url": url, "data": data})
        return DummyResponse(self.payload)


def build_store(tmp_path: Path, session: Optional[DummySession] = None) -> MoodleCredentialStore:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(path=config_path)
    manager.update_moodle_config(base_url="https://moodle.example.com")
    store = MoodleCredentialStore(manager, session=session or DummySession({"token": "dummy"}))
    store.backend = MemoryBackend()  # type: ignore[attr-defined]
    return store


def test_get_token_from_backend(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    metadata = store.config.get_moodle_config()
    store.backend.set(metadata["token_ref"], "secret-token")  # type: ignore[attr-defined]

    token = store.get_token(ensure_fresh=False)
    assert token == "secret-token"


def test_refresh_token_uses_private_token(tmp_path: Path) -> None:
    payload = {"token": "new-token", "privatetoken": "new-private"}
    session = DummySession(payload)
    store = build_store(tmp_path, session=session)

    metadata = store.config.get_moodle_config()
    store.backend.set(metadata["private_ref"], "refresh-private")  # type: ignore[attr-defined]

    token = store.refresh_token()
    assert token == "new-token"
    assert store.backend.get(metadata["token_ref"]) == "new-token"  # type: ignore[attr-defined]
    assert store.backend.get(metadata["private_ref"]) == "new-private"  # type: ignore[attr-defined]
    assert session.calls, "Expected refresh request to be issued"


def test_get_token_raises_when_missing(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    store.config.update_moodle_config(token="")

    with pytest.raises(CredentialError):
        store.get_token(ensure_fresh=False)