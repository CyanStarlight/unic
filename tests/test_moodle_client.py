from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from mgr.managerlib.moodle import MoodleClient, MoodleError


class DummyResponse:
    def __init__(self, payload: object, status_code: int = 200, content: bytes | None = None) -> None:
        self._payload = payload
        self.status_code = status_code
        self.content = content or b""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> object:
        return self._payload


def test_call_raises_on_moodle_exception() -> None:
    session = MagicMock()
    session.post.return_value = DummyResponse(
        {
            "exception": "moodle_exception",
            "errorcode": "invalidtoken",
            "message": "Invalid token",
        }
    )

    client = MoodleClient("https://moodle.example.com", "token", session=session)
    with pytest.raises(MoodleError):
        client.call("core_webservice_get_site_info")


def test_list_courses_requests_site_info_once() -> None:
    session = MagicMock()
    session.post.side_effect = [
        DummyResponse({"userid": 7}),
        DummyResponse([
            {"id": 1, "shortname": "COMP-101"},
            {"id": 2, "shortname": "MATH-101"},
        ]),
    ]

    client = MoodleClient("https://moodle.example.com", "token", session=session)
    courses = client.list_courses()

    assert len(courses) == 2
    assert session.post.call_count == 2


def test_download_file_appends_token(tmp_path: Path) -> None:
    file_response = MagicMock()
    file_response.raise_for_status.return_value = None
    file_response.content = b"hello"

    session = MagicMock()
    session.get.return_value = file_response
    session.post.return_value = DummyResponse({"userid": 1})

    client = MoodleClient("https://moodle.example.com", "token", session=session)
    destination = tmp_path / "file.txt"

    client.download_file({"fileurl": "https://moodle.example.com/file.php/1"}, destination)

    session.get.assert_called_with(
        "https://moodle.example.com/file.php/1?token=token", timeout=30
    )
    assert destination.read_bytes() == b"hello"
