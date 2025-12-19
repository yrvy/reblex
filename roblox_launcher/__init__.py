"""
Reblex - A Python Roblox Launcher

This module provides functionality to launch Roblox games from protocol URLs
(roblox-player://) without needing the official Roblox bootstrapper.
"""

__version__ = "1.0.0"
__author__ = "Reblex"

from .launcher import RobloxLauncher
from .protocol import parse_roblox_url, RobloxLaunchParams
from .finder import find_roblox_player

__all__ = [
    "RobloxLauncher",
    "parse_roblox_url",
    "RobloxLaunchParams",
    "find_roblox_player",
]
