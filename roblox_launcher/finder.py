"""
Roblox installation finder.

Locates the Roblox player executable on Windows systems.
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional
import glob


def get_local_appdata() -> Optional[Path]:
    """Get the LocalAppData directory path."""
    # Try environment variable first
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata)

    # Fallback for Windows
    if sys.platform == "win32":
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            return Path(userprofile) / "AppData" / "Local"

    return None


def find_roblox_versions_folder() -> Optional[Path]:
    """Find the Roblox Versions folder."""
    local_appdata = get_local_appdata()
    if not local_appdata:
        return None

    versions_path = local_appdata / "Roblox" / "Versions"
    if versions_path.exists():
        return versions_path

    return None


def find_roblox_player(version: Optional[str] = None) -> Optional[Path]:
    """
    Find the RobloxPlayerBeta.exe executable.

    Args:
        version: Specific version to find (e.g., "version-abc123").
                If None, finds the latest version.

    Returns:
        Path to RobloxPlayerBeta.exe or None if not found.
    """
    versions_folder = find_roblox_versions_folder()
    if not versions_folder:
        return None

    if version:
        # Look for specific version
        player_path = versions_folder / version / "RobloxPlayerBeta.exe"
        if player_path.exists():
            return player_path
        return None

    # Find the latest version by modification time
    version_dirs = []
    version_pattern = re.compile(r"^version-[a-f0-9]+$", re.IGNORECASE)

    for entry in versions_folder.iterdir():
        if entry.is_dir() and version_pattern.match(entry.name):
            player_exe = entry / "RobloxPlayerBeta.exe"
            if player_exe.exists():
                version_dirs.append((entry, player_exe.stat().st_mtime))

    if not version_dirs:
        return None

    # Sort by modification time, newest first
    version_dirs.sort(key=lambda x: x[1], reverse=True)
    return version_dirs[0][0] / "RobloxPlayerBeta.exe"


def find_roblox_studio(version: Optional[str] = None) -> Optional[Path]:
    """
    Find the RobloxStudioBeta.exe executable.

    Args:
        version: Specific version to find.
                If None, finds the latest version.

    Returns:
        Path to RobloxStudioBeta.exe or None if not found.
    """
    versions_folder = find_roblox_versions_folder()
    if not versions_folder:
        return None

    if version:
        studio_path = versions_folder / version / "RobloxStudioBeta.exe"
        if studio_path.exists():
            return studio_path
        return None

    # Find the latest Studio version
    version_dirs = []
    version_pattern = re.compile(r"^version-[a-f0-9]+$", re.IGNORECASE)

    for entry in versions_folder.iterdir():
        if entry.is_dir() and version_pattern.match(entry.name):
            studio_exe = entry / "RobloxStudioBeta.exe"
            if studio_exe.exists():
                version_dirs.append((entry, studio_exe.stat().st_mtime))

    if not version_dirs:
        return None

    version_dirs.sort(key=lambda x: x[1], reverse=True)
    return version_dirs[0][0] / "RobloxStudioBeta.exe"


def get_installed_versions() -> list[dict]:
    """
    Get a list of all installed Roblox versions.

    Returns:
        List of dicts with version info:
        [{"version": "version-xxx", "path": Path, "has_player": bool, "has_studio": bool}]
    """
    versions_folder = find_roblox_versions_folder()
    if not versions_folder:
        return []

    versions = []
    version_pattern = re.compile(r"^version-[a-f0-9]+$", re.IGNORECASE)

    for entry in versions_folder.iterdir():
        if entry.is_dir() and version_pattern.match(entry.name):
            has_player = (entry / "RobloxPlayerBeta.exe").exists()
            has_studio = (entry / "RobloxStudioBeta.exe").exists()

            if has_player or has_studio:
                versions.append({
                    "version": entry.name,
                    "path": entry,
                    "has_player": has_player,
                    "has_studio": has_studio,
                    "mtime": entry.stat().st_mtime
                })

    # Sort by modification time, newest first
    versions.sort(key=lambda x: x["mtime"], reverse=True)
    return versions


def find_roblox_app_settings() -> Optional[Path]:
    """Find the Roblox AppSettings.xml file."""
    local_appdata = get_local_appdata()
    if not local_appdata:
        return None

    settings_path = local_appdata / "Roblox" / "GlobalBasicSettings_13.xml"
    if settings_path.exists():
        return settings_path

    return None
