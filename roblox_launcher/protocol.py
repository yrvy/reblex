"""
Protocol URL parsing for Roblox launcher URLs.

Handles parsing of roblox-player:// protocol URLs into structured launch parameters.
"""

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse, parse_qs, unquote
import time


@dataclass
class RobloxLaunchParams:
    """Parameters extracted from a roblox-player:// URL."""

    # Core launch parameters
    launch_mode: str = "play"
    game_info: Optional[str] = None  # Authentication token
    place_launcher_url: Optional[str] = None

    # Game identification
    place_id: Optional[str] = None
    game_instance_id: Optional[str] = None

    # Timing and tracking
    launch_time: Optional[int] = None
    browser_tracker_id: Optional[str] = None

    # Locale settings
    roblox_locale: str = "en_us"
    game_locale: str = "en_us"

    # Channel (update channel)
    channel: str = ""

    # Optional join parameters
    access_code: Optional[str] = None
    link_code: Optional[str] = None
    launch_data: Optional[str] = None

    # Request type
    request: Optional[str] = None

    # Raw parameters for any extras
    raw_params: dict = field(default_factory=dict)

    def to_launch_args(self) -> list[str]:
        """Convert parameters to command-line arguments for RobloxPlayerBeta."""
        args = []

        # Add launch mode
        if self.launch_mode:
            args.append(f"--launchmode={self.launch_mode}")

        # Add game info (auth token)
        if self.game_info:
            args.append(f"--gameinfo={self.game_info}")

        # Add place launcher URL
        if self.place_launcher_url:
            args.append(f"--placelauncherurl={self.place_launcher_url}")

        # Add launch time
        if self.launch_time:
            args.append(f"--launchtime={self.launch_time}")
        else:
            args.append(f"--launchtime={int(time.time() * 1000)}")

        # Add browser tracker ID
        if self.browser_tracker_id:
            args.append(f"--browsertrackerid={self.browser_tracker_id}")

        # Add locale settings
        if self.roblox_locale:
            args.append(f"--robloxLocale={self.roblox_locale}")
        if self.game_locale:
            args.append(f"--gameLocale={self.game_locale}")

        # Add channel if specified
        if self.channel:
            args.append(f"--channel={self.channel}")

        # Add optional parameters
        if self.access_code:
            args.append(f"--accesscode={self.access_code}")
        if self.link_code:
            args.append(f"--linkcode={self.link_code}")
        if self.launch_data:
            args.append(f"--launchdata={self.launch_data}")

        return args


def parse_roblox_url(url: str) -> RobloxLaunchParams:
    """
    Parse a roblox-player:// protocol URL into launch parameters.

    Args:
        url: The roblox-player:// URL to parse

    Returns:
        RobloxLaunchParams with extracted values

    Example URL:
        roblox-player:1+launchmode:play+gameinfo:TOKEN+placelauncherurl:URL+launchtime:123
    """
    params = RobloxLaunchParams()

    # Handle empty or invalid URLs
    if not url:
        return params

    # Remove the protocol prefix
    url = url.strip()
    if url.startswith("roblox-player://"):
        url = url[16:]
    elif url.startswith("roblox-player:"):
        url = url[14:]

    # Roblox uses + as delimiter between parameters and : between key/value
    # Format: 1+key:value+key:value+...
    parts = url.split("+")

    raw_params = {}
    for part in parts:
        if ":" in part:
            # Split only on first colon (values may contain colons)
            key, value = part.split(":", 1)
            key = key.lower().strip()
            value = unquote(value.strip())
            raw_params[key] = value

    # Map to structured parameters
    params.raw_params = raw_params

    params.launch_mode = raw_params.get("launchmode", "play")
    params.game_info = raw_params.get("gameinfo")
    params.place_launcher_url = raw_params.get("placelauncherurl")
    params.place_id = raw_params.get("placeid")
    params.game_instance_id = raw_params.get("gameinstanceid")

    # Parse launch time
    launch_time_str = raw_params.get("launchtime")
    if launch_time_str:
        try:
            params.launch_time = int(launch_time_str)
        except ValueError:
            pass

    params.browser_tracker_id = raw_params.get("browsertrackerid")
    params.roblox_locale = raw_params.get("robloxlocale", "en_us")
    params.game_locale = raw_params.get("gamelocale", "en_us")
    params.channel = raw_params.get("channel", "")
    params.access_code = raw_params.get("accesscode")
    params.link_code = raw_params.get("linkcode")
    params.launch_data = raw_params.get("launchdata")
    params.request = raw_params.get("request")

    return params


def build_roblox_url(
    place_id: str,
    game_info: Optional[str] = None,
    launch_mode: str = "play",
    **kwargs
) -> str:
    """
    Build a roblox-player:// URL from parameters.

    Args:
        place_id: The Roblox place ID to launch
        game_info: Authentication token (optional)
        launch_mode: Launch mode (default: "play")
        **kwargs: Additional parameters

    Returns:
        A roblox-player:// protocol URL
    """
    parts = ["1"]

    parts.append(f"launchmode:{launch_mode}")

    if game_info:
        parts.append(f"gameinfo:{game_info}")

    if place_id:
        parts.append(f"placeid:{place_id}")

    parts.append(f"launchtime:{int(time.time() * 1000)}")

    # Add any extra parameters
    for key, value in kwargs.items():
        if value is not None:
            parts.append(f"{key}:{value}")

    return "roblox-player:" + "+".join(parts)
