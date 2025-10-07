"""Core functionality for the UNIC repository manager."""

from .config import ConfigManager, ConfigError
from .credentials import CredentialError, MoodleCredentialStore
from .moodle import MoodleClient, MoodleSyncService, MoodleError

__all__ = [
    "ConfigManager",
    "ConfigError",
    "CredentialError",
    "MoodleCredentialStore",
    "MoodleClient",
    "MoodleSyncService",
    "MoodleError",
]
