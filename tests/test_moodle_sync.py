from __future__ import annotations

from pathlib import Path
from types import MethodType

from mgr.managerlib.moodle import MoodleSyncService


class FakeClient:
    def __init__(self) -> None:
        self.downloaded: list[Path] = []

    def list_courses(self):
        return [{"id": 101, "shortname": "COMP-113"}]

    def get_course_contents(self, course_id: int):  # noqa: D401
        return [
            {
                "id": 10,
                "name": "Week 1",
                "modules": [
                    {
                        "id": 20,
                        "name": "Slides",
                        "contents": [
                            {
                                "type": "file",
                                "filename": "Lecture 1.pdf",
                                "fileurl": "https://example.com/lecture-1.pdf",
                                "filesize": 512,
                            }
                        ],
                    }
                ],
            }
        ]

    def download_file(self, file_info: dict, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"demo")
        self.downloaded.append(destination)
        return destination


def test_sync_creates_course_structure(tmp_path: Path) -> None:
    client = FakeClient()
    service = MoodleSyncService(client, tmp_path, download_files=True)

    summary = service.sync()

    assert summary and summary[0]["shortname"] == "COMP-113"
    course_dir = tmp_path / "COMP-113" / "101"
    assert (course_dir / "course.json").exists()
    assert (course_dir / "contents.json").exists()
    for folder in ("Assignments", "Homework", "Notes", "Books"):
        assert (course_dir / folder).is_dir()
    assert client.downloaded, "Expected file downloads when download_files=True"
    assert client.downloaded[0].is_relative_to(course_dir / "Assignments")


def test_sync_honours_course_filter(tmp_path: Path) -> None:
    client = FakeClient()
    service = MoodleSyncService(client, tmp_path)

    summary = service.sync(course_filter=["MATH-999"])
    assert summary == []
    assert not (tmp_path / "COMP-113").exists()


def test_sync_skips_large_files(tmp_path: Path) -> None:
    client = FakeClient()

    def oversized_contents(self, course_id: int):
        return [
            {
                "id": 10,
                "name": "Week",
                "modules": [
                    {
                        "id": 20,
                        "name": "Videos",
                        "contents": [
                            {
                                "type": "file",
                                "filename": "Large.mp4",
                                "fileurl": "https://example.com/large.mp4",
                                "filesize": 50 * 1024 * 1024,
                            }
                        ],
                    }
                ],
            }
        ]

    client.get_course_contents = MethodType(oversized_contents, client)  # type: ignore[assignment]

    service = MoodleSyncService(client, tmp_path, download_files=True, max_file_size=1024)
    service.sync()

    assert not client.downloaded, "Large files should be skipped when exceeding max size"
