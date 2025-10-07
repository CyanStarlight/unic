#!/usr/bin/env python3
from __future__ import annotations

import logging
import getpass
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

try:
    # Running as a module: python -m mgr.mgr
    from .managerlib.config import ConfigError, ConfigManager
    from .managerlib.credentials import CredentialError, MoodleCredentialStore
    from .managerlib.moodle import MoodleClient, MoodleError, MoodleSyncService
except ImportError:  # pragma: no cover - fallback for direct execution
    CURRENT_DIR = Path(__file__).resolve().parent
    if str(CURRENT_DIR) not in sys.path:
        sys.path.append(str(CURRENT_DIR))
    from managerlib.config import ConfigError, ConfigManager  # type: ignore
    from managerlib.credentials import CredentialError, MoodleCredentialStore  # type: ignore
    from managerlib.moodle import MoodleClient, MoodleError, MoodleSyncService  # type: ignore


logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger("unic-manager")


class RepoManager:
    """Interactive helper for common repository maintenance tasks."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.config = ConfigManager()

    # ------------------------------------------------------------------
    # Interactive CLI
    # ------------------------------------------------------------------
    def run(self) -> None:
        print(f"Current repository path: {self.repo_path}")

        actions = {
            "1": self.handle_search,
            "2": self.handle_add_course_manually,
            "3": self.sync_from_moodle,
            "4": self.configure_moodle_settings,
            "5": self.exit_program,
        }

        while True:
            print(
                "\nChoose an action:\n"
                "1. Search for a folder\n"
                "2. Add a new folder from course URL\n"
                "3. Sync courses from Moodle\n"
                "4. Configure Moodle credentials\n"
                "5. Exit"
            )

            action = input("Selection: ").strip()
            handler = actions.get(action)
            if handler is None:
                print("Invalid choice. Please choose a valid option.")
                continue
            handler()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def handle_search(self) -> None:
        query = input("Enter search query: ").strip()
        if not query:
            print("Query cannot be empty.")
            return

        matches = self.search_repo(query)
        if not matches:
            print("No matching folders found.")
            return

        for index, match in enumerate(matches, start=1):
            print(f"{index}. {match.relative_to(self.repo_path)}")

        choice = input(
            "Enter the number of a folder to convert it to a submodule, or press Enter to skip: "
        ).strip()
        if not choice:
            return

        try:
            selected = matches[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return

        self.convert_to_submodule(selected)

    def handle_add_course_manually(self) -> None:
        raw_input = input(
            "Enter course code followed by URL (e.g., MATH-101 https://portal.unic.ac.cy/courses/355025): "
        ).strip()
        try:
            course_code, course_id = self.parse_course_input(raw_input)
        except ValueError as exc:
            print(f"{exc}")
            return

        course_dir = self.create_course_directory(course_code, course_id)
        self.stage_and_commit(course_dir, f"Add course folder: {course_code}")

    def sync_from_moodle(self) -> None:
        try:
            base_url = self.config.require_moodle_base_url()
        except ConfigError as exc:
            print(exc)
            return

        credential_store = MoodleCredentialStore(self.config)
        try:
            token = credential_store.get_token()
        except CredentialError as exc:
            print(f"Cannot proceed without a Moodle token: {exc}")
            return

        moodle_config = self.config.effective_moodle_config()

        client = MoodleClient(base_url, token)
        sync_service = MoodleSyncService(
            client,
            self.repo_path,
            download_files=bool(moodle_config.get("download_files")),
            max_file_size=moodle_config.get("max_file_size"),
            logger=LOGGER,
        )

        raw_filter = input(
            "Optional: provide comma-separated course codes or IDs to limit the sync: "
        ).strip()
        course_filter = [item.strip() for item in raw_filter.split(",") if item.strip()]
        if not course_filter:
            course_filter = None

        print("Starting Moodle sync...")
        try:
            summary = sync_service.sync(course_filter=course_filter)
        except (MoodleError, OSError) as exc:
            print(f"Sync failed: {exc}")
            return

        if not summary:
            print("No courses matched the provided filter." if course_filter else "No courses returned from Moodle.")
            return

        print("Sync completed. Updated courses:")
        for item in summary:
            print(f"- {item['shortname']} ({item['id']}): {item['path']}")

    def configure_moodle_settings(self) -> None:
        current = self.config.get_moodle_config()
        credential_store = MoodleCredentialStore(self.config)
        print("Configure Moodle settings (leave blank to keep current value).")
        base_url = input(
            f"Base URL [{current['base_url'] or 'https://moodle.example.com'}]: "
        ).strip() or current["base_url"]

        token_hint = "stored" if credential_store.has_token() else "missing"
        token_input = input(
            f"API token (leave blank to keep {token_hint}, '-' to remove): "
        ).strip()

        private_status = "present" if credential_store.has_private_token() else "missing"
        private_input = input(
            f"Private token for auto-refresh (current: {private_status}) [Enter to keep, '-' to remove]: "
        ).strip()

        username_input = input(
            f"Username for auto-refresh [{current.get('username') or '(none)'}]: "
        ).strip()

        password_prompt = getpass.getpass(
            "Moodle password for auto-refresh (leave blank to keep current, '-' to remove): "
        )

        download_default = "y" if current.get("download_files") else "n"
        download_choice = input(
            f"Download attached files? (y/n) [{download_default}]: "
        ).strip().lower()
        if download_choice not in {"y", "n", ""}:
            print("Invalid choice for file downloads; keeping existing value.")
            download_choice = ""
        download_files = (
            current.get("download_files")
            if download_choice == ""
            else download_choice == "y"
        )

        max_size_input = input(
            f"Maximum file size in bytes (0 to disable limit) [{current.get('max_file_size')}]: "
        ).strip()
        try:
            max_size = (
                None
                if max_size_input == ""
                else int(max_size_input) if int(max_size_input) > 0 else None
            )
        except ValueError:
            print("Invalid number; keeping existing limit.")
            max_size = current.get("max_file_size")

        ttl_input = input(
            f"Token refresh interval in hours (0 to disable) [{current.get('token_ttl_hours')}]: "
        ).strip()
        try:
            ttl_value = (
                current.get("token_ttl_hours")
                if ttl_input == ""
                else int(ttl_input) if int(ttl_input) > 0 else 0
            )
        except ValueError:
            print("Invalid number; keeping existing refresh interval.")
            ttl_value = current.get("token_ttl_hours")

        username_value: Optional[str]
        if username_input == "-":
            username_value = ""
        elif username_input == "":
            username_value = current.get("username", "")
        else:
            username_value = username_input

        try:
            self.config.update_moodle_config(
                base_url=base_url,
                download_files=download_files,
                max_file_size=max_size,
                token_ttl_hours=ttl_value,
                username=username_value,
            )
        except ConfigError as exc:
            print(f"Failed to update configuration: {exc}")
            return

        def normalize_secret(value: str, *, allow_delete: bool = True) -> Optional[str]:
            if value == "":
                return None
            if allow_delete and value == "-":
                return ""
            return value

        token_value = normalize_secret(token_input)
        private_value = normalize_secret(private_input)
        if password_prompt == "-":
            password_value: Optional[str] = ""
        elif password_prompt == "":
            password_value = None
        else:
            password_value = password_prompt

        try:
            credential_store.store_credentials(
                token=token_value,
                private_token=private_value,
                username=username_value,
                password=password_value,
            )
        except CredentialError as exc:
            print(f"Failed to store secrets: {exc}")
            return

        print("Moodle configuration saved.")
        print(json_summary(self.config.get_moodle_config()))

    def exit_program(self) -> None:
        print("Goodbye!")
        raise SystemExit(0)

    # ------------------------------------------------------------------
    # Core utilities
    # ------------------------------------------------------------------
    def search_repo(self, query: str) -> List[Path]:
        query_lower = query.lower()
        matches: List[Path] = []
        for path in self.repo_path.rglob("*"):
            if path.is_dir() and query_lower in path.name.lower():
                matches.append(path)
        return matches

    def convert_to_submodule(self, folder: Path) -> None:
        if not (folder / ".git").exists():
            print(f"{folder} is not a git repository; initialize it first if needed.")
            return

        rel_path = folder.relative_to(self.repo_path)
        print(f"Adding submodule for {rel_path}...")
        result = subprocess.run(
            ["git", "submodule", "add", str(folder), str(rel_path)],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Failed to add submodule: {result.stderr.strip()}")
            return
        self.stage_and_commit(folder, f"Convert {rel_path} to submodule")

    def create_course_directory(self, course_code: str, course_id: str) -> Path:
        course_dir = self.repo_path / course_code / course_id
        course_dir.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directories: {course_dir.relative_to(self.repo_path)}")
        return course_dir

    def stage_and_commit(self, path: Path, message: str) -> None:
        rel_path = path.relative_to(self.repo_path)
        subprocess.run(["git", "add", str(rel_path)], cwd=self.repo_path, check=False)
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"Committed changes: {message}")
        else:
            print("Nothing committed (maybe no changes or git reported an error).")

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------
    @staticmethod
    def parse_course_input(raw: str) -> tuple[str, str]:
        parts = raw.split()
        if len(parts) < 2:
            raise ValueError("Input must contain a course code followed by a URL.")
        course_code = parts[0]
        url = parts[1]
        parsed = urlparse(url)
        course_id = Path(parsed.path).name
        if not course_id:
            raise ValueError("Unable to determine course id from URL.")
        return course_code, course_id


def json_summary(payload: dict) -> str:
    return "\n".join(f"  {key}: {value}" for key, value in payload.items())


def main() -> None:
    repo_path = Path(__file__).resolve().parent.parent
    manager = RepoManager(repo_path)
    manager.run()


if __name__ == "__main__":
    main()
