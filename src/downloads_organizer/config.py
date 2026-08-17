"""Configuration loading and validation for Downloads Organizer."""

import json
from pathlib import Path

DEFAULT_CATEGORIES = {
    "Documents": [".pdf", ".docx", ".txt", ".rtf", ".xlsx", ".pptx", ".md"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp", ".webp"],
    "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".webm"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Executables": [".exe", ".msi", ".dmg", ".pkg", ".deb"],
    "Scripts": [".py", ".js", ".sh", ".bat", ".ps1"],
}
DEFAULT_CATEGORY = "Miscellaneous"


def load_categories(config_path=None):
    """Load optional category overrides from JSON and validate their shape."""
    if config_path is None:
        return DEFAULT_CATEGORIES.copy(), DEFAULT_CATEGORY

    path = Path(config_path)
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file does not exist: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON configuration: {exc.msg}") from exc

    categories = data.get("categories")
    if not isinstance(categories, dict) or not categories:
        raise ValueError("Configuration 'categories' must be a non-empty object")

    normalized = {}
    for name, extensions in categories.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Category names must be non-empty strings")
        if not isinstance(extensions, list):
            raise ValueError(f"Extensions for '{name}' must be a list")
        if not all(isinstance(ext, str) and ext.startswith(".") for ext in extensions):
            raise ValueError(f"Extensions for '{name}' must be strings beginning with '.'")
        normalized[name] = [ext.lower() for ext in extensions]

    fallback = data.get("fallback", DEFAULT_CATEGORY)
    if not isinstance(fallback, str) or not fallback.strip():
        raise ValueError("Configuration 'fallback' must be a non-empty string")

    return normalized, fallback
