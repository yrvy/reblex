"""
Roblox player launcher.

Handles finding the Roblox installation and launching the player.
"""

import os
import sys
import subprocess
import time
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from urllib.parse import quote

from .client import RobloxClient


@dataclass
class LaunchResult:
    """Result of a game launch."""
    success: bool
    message: str
    process: Optional[subprocess.Popen] = None


class RobloxLauncher:
    """
    Roblox game launcher.

    Handles:
    - Finding Roblox installation
    - Building launch URLs
    - Launching the Roblox player
    """

    def __init__(self, client: RobloxClient, player_path: Optional[str] = None):
        """
        Initialize the launcher.

        Args:
            client: RobloxClient instance for API calls
            player_path: Optional explicit path to RobloxPlayerBeta.exe
        """
        self._client = client
        self._player_path = Path(player_path) if player_path else None

    @staticmethod
    def find_roblox_player() -> Optional[Path]:
        """
        Find the RobloxPlayerBeta.exe on Windows.

        Searches in %LOCALAPPDATA%/Roblox/Versions/

        Returns:
            Path to RobloxPlayerBeta.exe or None
        """
        if sys.platform != "win32":
            return None

        local_appdata = os.environ.get("LOCALAPPDATA")
        if not local_appdata:
            return None

        versions_path = Path(local_appdata) / "Roblox" / "Versions"
        if not versions_path.exists():
            return None

        # Find the latest version
        version_pattern = re.compile(r"^version-[a-f0-9]+$", re.IGNORECASE)
        version_dirs = []

        for entry in versions_path.iterdir():
            if entry.is_dir() and version_pattern.match(entry.name):
                player_exe = entry / "RobloxPlayerBeta.exe"
                if player_exe.exists():
                    version_dirs.append((player_exe, player_exe.stat().st_mtime))

        if not version_dirs:
            return None

        # Return the most recently modified
        version_dirs.sort(key=lambda x: x[1], reverse=True)
        return version_dirs[0][0]

    @property
    def player_path(self) -> Optional[Path]:
        """Get the path to RobloxPlayerBeta.exe."""
        if self._player_path:
            return self._player_path
        return self.find_roblox_player()

    @property
    def is_installed(self) -> bool:
        """Check if Roblox is installed."""
        path = self.player_path
        return path is not None and path.exists()

    def build_launch_url(
        self,
        auth_ticket: str,
        place_id: int,
        job_id: Optional[str] = None,
        link_code: Optional[str] = None,
        launch_data: Optional[str] = None,
    ) -> str:
        """
        Build a roblox-player:// launch URL.

        Args:
            auth_ticket: Authentication ticket from get_auth_ticket()
            place_id: Place ID to join
            job_id: Specific server instance ID (optional)
            link_code: Deep link code (optional)
            launch_data: Custom launch data (optional)

        Returns:
            The roblox-player:// URL
        """
        launch_time = int(time.time() * 1000)
        browser_tracker_id = str(int(time.time() * 1000000))

        # Build the place launcher URL
        place_launcher_url = (
            f"https://assetgame.roblox.com/game/PlaceLauncher.ashx"
            f"?request=RequestGame&placeId={place_id}"
        )
        if job_id:
            place_launcher_url += f"&gameId={job_id}"

        parts = [
            "1",
            "launchmode:play",
            f"gameinfo:{auth_ticket}",
            f"launchtime:{launch_time}",
            f"placelauncherurl:{quote(place_launcher_url, safe='')}",
            f"browsertrackerid:{browser_tracker_id}",
            "robloxLocale:en_us",
            "gameLocale:en_us",
            "channel:",
            "LaunchExp:InApp",
        ]

        if link_code:
            parts.append(f"linkCode:{link_code}")
        if launch_data:
            parts.append(f"launchData:{quote(launch_data, safe='')}")

        return "roblox-player:" + "+".join(parts)

    async def launch(
        self,
        place_id: int,
        job_id: Optional[str] = None,
        link_code: Optional[str] = None,
        launch_data: Optional[str] = None,
        use_shell: bool = True,
    ) -> LaunchResult:
        """
        Launch a Roblox game.

        Args:
            place_id: The place ID to join
            job_id: Specific server instance ID (optional)
            link_code: Deep link code (optional)
            launch_data: Custom launch data (optional)
            use_shell: Whether to use shell.open (True) or direct exe (False)

        Returns:
            LaunchResult with success status
        """
        # Get authentication ticket
        auth_ticket = await self._client.get_auth_ticket()
        if not auth_ticket:
            return LaunchResult(
                success=False,
                message="Failed to get authentication ticket. Check your cookie."
            )

        # Build launch URL
        launch_url = self.build_launch_url(
            auth_ticket=auth_ticket,
            place_id=place_id,
            job_id=job_id,
            link_code=link_code,
            launch_data=launch_data,
        )

        if use_shell:
            # Use the OS to handle the protocol URL
            return self._launch_via_protocol(launch_url)
        else:
            # Launch the exe directly
            return self._launch_direct(launch_url)

    def _launch_via_protocol(self, launch_url: str) -> LaunchResult:
        """Launch using the roblox-player:// protocol handler."""
        try:
            if sys.platform == "win32":
                os.startfile(launch_url)
            elif sys.platform == "darwin":
                subprocess.run(["open", launch_url], check=True)
            else:
                subprocess.run(["xdg-open", launch_url], check=True)

            return LaunchResult(
                success=True,
                message="Game launched via protocol handler"
            )
        except Exception as e:
            return LaunchResult(
                success=False,
                message=f"Failed to launch: {e}"
            )

    def _launch_direct(self, launch_url: str) -> LaunchResult:
        """Launch by directly running RobloxPlayerBeta.exe."""
        player = self.player_path
        if not player or not player.exists():
            return LaunchResult(
                success=False,
                message="Roblox player not found"
            )

        try:
            # Parse the URL into arguments
            args = self._url_to_args(launch_url)

            process = subprocess.Popen(
                [str(player)] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32" else 0
            )

            return LaunchResult(
                success=True,
                message="Game launched directly",
                process=process
            )
        except Exception as e:
            return LaunchResult(
                success=False,
                message=f"Failed to launch: {e}"
            )

    def _url_to_args(self, url: str) -> list[str]:
        """Convert a roblox-player:// URL to command-line arguments."""
        # Remove protocol prefix
        if url.startswith("roblox-player:"):
            url = url[14:]

        args = []
        parts = url.split("+")

        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                args.append(f"--{key}={value}")

        return args

    async def launch_to_server(
        self,
        place_id: int,
        server_index: int = 0,
    ) -> LaunchResult:
        """
        Launch and join a specific server by index.

        Args:
            place_id: The place ID
            server_index: Which server to join (0 = first/most populated)

        Returns:
            LaunchResult with success status
        """
        servers = await self._client.get_servers(place_id, limit=server_index + 1)

        if not servers:
            return LaunchResult(
                success=False,
                message="No servers available"
            )

        if server_index >= len(servers):
            return LaunchResult(
                success=False,
                message=f"Server index {server_index} not available"
            )

        server = servers[server_index]
        return await self.launch(place_id, job_id=server.job_id)
