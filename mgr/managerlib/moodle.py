from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import requests

__all__ = ["MoodleClient", "MoodleSyncService", "MoodleError"]

LOGGER = logging.getLogger(__name__)


class MoodleError(RuntimeError):
    """Raised when Moodle returns an error response."""


class MoodleClient:
    """Minimal REST client for Moodle web services."""

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ) -> None:
        if not base_url:
            raise ValueError("base_url must be provided")
        if not token:
            raise ValueError("token must be provided")

        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = session or requests.Session()
        self.timeout = timeout
        self._site_info: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Core HTTP helpers
    # ------------------------------------------------------------------
    def _rest_endpoint(self) -> str:
        return f"{self.base_url}/webservice/rest/server.php"

    def _prepare_payload(self, function: str, params: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "wstoken": self.token,
            "wsfunction": function,
            "moodlewsrestformat": "json",
        }

        for key, value in params.items():
            if isinstance(value, bool):
                payload[key] = int(value)
            else:
                payload[key] = value
        return payload

    def call(self, function: str, **params: Any) -> Any:
        payload = self._prepare_payload(function, params)
        response = self.session.post(
            self._rest_endpoint(), data=payload, timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and data.get("exception"):
            message = data.get("message", "Moodle returned an exception")
            error_code = data.get("errorcode", "unknown")
            raise MoodleError(f"{message} ({error_code})")
        return data

    # ------------------------------------------------------------------
    # High-level Moodle helpers
    # ------------------------------------------------------------------
    def get_site_info(self) -> Dict[str, Any]:
        if self._site_info is None:
            self._site_info = self.call("core_webservice_get_site_info")
        return self._site_info

    def list_courses(self) -> List[Dict[str, Any]]:
        site_info = self.get_site_info()
        user_id = site_info.get("userid")
        if not user_id:
            raise MoodleError("The Moodle token does not expose a user id.")
        courses = self.call("core_enrol_get_users_courses", userid=user_id)
        if not isinstance(courses, list):
            raise MoodleError("Unexpected Moodle response when listing courses")
        return courses

    def get_course_contents(
        self,
        course_id: int,
        *,
        options: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"courseid": course_id}
        if options:
            for index, option in enumerate(options):
                payload[f"options[{index}][name]"] = option["name"]
                payload[f"options[{index}][value]"] = option.get("value", "")
        contents = self.call("core_course_get_contents", **payload)
        if not isinstance(contents, list):
            raise MoodleError("Unexpected Moodle response when retrieving course contents")
        return contents

    def download_file(self, file_info: Dict[str, Any], destination: Path) -> Path:
        url = file_info.get("fileurl")
        if not url:
            raise MoodleError("File metadata missing 'fileurl'")
        url = self._with_token(url)
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "wb") as fh:
            fh.write(response.content)
        return destination

    def _with_token(self, url: str) -> str:
        if "token=" in url:
            return url
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}token={self.token}"


class MoodleSyncService:
    """Synchronises Moodle course data into the local repository."""

    def __init__(
        self,
        client: MoodleClient,
        repo_path: Path | str,
        *,
        download_files: bool = False,
        max_file_size: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.client = client
        self.repo_path = Path(repo_path)
        self.download_files = download_files
        self.max_file_size = max_file_size
        self.logger = logger or LOGGER

    def sync(
        self,
        *,
        course_filter: Optional[Iterable[str]] = None,
    ) -> List[Dict[str, Any]]:
        course_filter_set = {c.lower() for c in course_filter} if course_filter else None
        summary: List[Dict[str, Any]] = []

        for course in self.client.list_courses():
            if course_filter_set and not self._matches(course, course_filter_set):
                continue
            course_dir = self._sync_course(course)
            summary.append(
                {
                    "id": course.get("id"),
                    "shortname": course.get("shortname"),
                    "path": str(course_dir),
                }
            )
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _matches(self, course: Dict[str, Any], allowed: set[str]) -> bool:
        identifiers = {
            str(course.get("id", "")).lower(),
            str(course.get("shortname", "")).lower(),
            str(course.get("idnumber", "")).lower(),
        }
        return any(identifier in allowed for identifier in identifiers)

    def _sync_course(self, course: Dict[str, Any]) -> Path:
        course_dir = self._course_directory(course)
        course_dir.mkdir(parents=True, exist_ok=True)

        self._ensure_course_structure(course_dir)

        contents = self.client.get_course_contents(int(course["id"]))
        self._write_json(course_dir / "course.json", course)
        self._write_json(course_dir / "contents.json", contents)

        if self.download_files:
            self._download_from_contents(course_dir, contents)
        return course_dir

    def _course_directory(self, course: Dict[str, Any]) -> Path:
        course_code = self._course_code(course)
        course_id = str(course.get("id", ""))
        return self.repo_path / course_code / course_id

    def _download_from_contents(self, course_dir: Path, contents: List[Dict[str, Any]]) -> None:
        assignments_root = course_dir / "Assignments"
        assignments_root.mkdir(parents=True, exist_ok=True)
        for section in contents:
            section_name = section.get("name") or f"section-{section.get('id', 'unknown')}"
            section_dir = assignments_root / self._slugify(section_name)
            for module in section.get("modules", []):
                module_name = module.get("name") or f"module-{module.get('id', 'unknown')}"
                module_dir = section_dir / self._slugify(module_name)
                for file_info in module.get("contents", []):
                    if file_info.get("type") != "file":
                        continue
                    if self._should_skip_file(file_info):
                        continue
                    filename = file_info.get("filename") or "file"
                    destination = module_dir / self._safe_filename(filename)
                    try:
                        self.client.download_file(file_info, destination)
                    except Exception as exc:  # pylint: disable=broad-except
                        self.logger.warning(
                            "Failed to download %s for course %s: %s",
                            filename,
                            course_dir.name,
                            exc,
                        )

    def _ensure_course_structure(self, course_dir: Path) -> None:
        for name in ("Assignments", "Homework", "Notes", "Books"):
            (course_dir / name).mkdir(parents=True, exist_ok=True)

    def _course_code(self, course: Dict[str, Any]) -> str:
        shortname = str(course.get("shortname") or "")
        code = self._extract_course_code(shortname)
        if not code:
            fullname = str(course.get("fullname") or "")
            code = self._extract_course_code(fullname)
        if code:
            return code

        fallback = shortname or f"COURSE-{course.get('id', '')}"
        slug = self._slugify(fallback)
        return slug.upper() if slug else f"COURSE-{course.get('id', '')}"

    @staticmethod
    def _extract_course_code(value: str) -> Optional[str]:
        match = re.search(r"([A-Za-z]{2,})\s*[-_/ ]?\s*(\d{2,4})", value)
        if not match:
            return None
        subject, number = match.groups()
        return f"{subject.upper()}-{number}"

    def _should_skip_file(self, file_info: Dict[str, Any]) -> bool:
        if self.max_file_size is None:
            return False
        size = file_info.get("filesize")
        if size is None:
            return False
        try:
            size_int = int(size)
        except (TypeError, ValueError):
            return False
        if size_int > self.max_file_size:
            self.logger.info(
                "Skipping %s (%s bytes) because it exceeds the configured limit",
                file_info.get("filename", "file"),
                size_int,
            )
            return True
        return False

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    @staticmethod
    def _slugify(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9\-_.]+", "-", value)
        value = re.sub(r"-+", "-", value)
        return value.strip("-") or "item"

    @staticmethod
    def _safe_filename(value: str) -> str:
        value = value.replace("/", "_").replace("\\", "_")
        value = re.sub(r"[<>:\\|?*]", "_", value)
        value = value.strip()
        return value or "file"
