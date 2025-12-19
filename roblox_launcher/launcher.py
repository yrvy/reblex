"""
Main Roblox launcher module.

Provides the RobloxLauncher class for launching Roblox games.
"""

import subprocess
import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass

from .finder import find_roblox_player, find_roblox_studio, get_installed_versions
from .protocol import parse_roblox_url, RobloxLaunchParams


logger = logging.getLogger(__name__)


@dataclass
class LaunchResult:
    """Result of a launch operation."""
    success: bool
    process: Optional[subprocess.Popen] = None
    error: Optional[str] = None
    player_path: Optional[Path] = None


class RobloxLauncher:
    """
    Roblox game launcher.

    Handles launching Roblox games from protocol URLs or direct parameters.
    """

    def __init__(
        self,
        player_path: Optional[Union[str, Path]] = None,
        version: Optional[str] = None
    ):
        """
        Initialize the launcher.

        Args:
            player_path: Direct path to RobloxPlayerBeta.exe.
                        If None, will auto-detect.
            version: Specific Roblox version to use.
                    If None, uses the latest version.
        """
        self._player_path: Optional[Path] = None
        self._version = version

        if player_path:
            self._player_path = Path(player_path)
        else:
            self._player_path = find_roblox_player(version)

    @property
    def player_path(self) -> Optional[Path]:
        """Get the path to the Roblox player executable."""
        return self._player_path

    @property
    def is_available(self) -> bool:
        """Check if Roblox player is available."""
        return self._player_path is not None and self._player_path.exists()

    def launch_url(
        self,
        url: str,
        wait: bool = False,
        extra_args: Optional[list[str]] = None
    ) -> LaunchResult:
        """
        Launch Roblox from a protocol URL.

        Args:
            url: The roblox-player:// URL
            wait: Whether to wait for the process to complete
            extra_args: Additional command-line arguments

        Returns:
            LaunchResult with process info
        """
        params = parse_roblox_url(url)
        return self.launch_params(params, wait=wait, extra_args=extra_args)

    def launch_params(
        self,
        params: RobloxLaunchParams,
        wait: bool = False,
        extra_args: Optional[list[str]] = None
    ) -> LaunchResult:
        """
        Launch Roblox with specific parameters.

        Args:
            params: Launch parameters
            wait: Whether to wait for the process to complete
            extra_args: Additional command-line arguments

        Returns:
            LaunchResult with process info
        """
        if not self.is_available:
            return LaunchResult(
                success=False,
                error="Roblox player not found. Please install Roblox first."
            )

        args = [str(self._player_path)]
        args.extend(params.to_launch_args())

        if extra_args:
            args.extend(extra_args)

        logger.info(f"Launching Roblox: {' '.join(args)}")

        try:
            if wait:
                result = subprocess.run(args, capture_output=True, text=True)
                return LaunchResult(
                    success=result.returncode == 0,
                    player_path=self._player_path,
                    error=result.stderr if result.returncode != 0 else None
                )
            else:
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                    if sys.platform == "win32" else 0
                )
                return LaunchResult(
                    success=True,
                    process=process,
                    player_path=self._player_path
                )
        except Exception as e:
            logger.error(f"Failed to launch Roblox: {e}")
            return LaunchResult(
                success=False,
                error=str(e),
                player_path=self._player_path
            )

    def launch_place(
        self,
        place_id: str,
        game_info: Optional[str] = None,
        job_id: Optional[str] = None,
        wait: bool = False
    ) -> LaunchResult:
        """
        Launch a specific Roblox place.

        Args:
            place_id: The Roblox place ID
            game_info: Authentication token
            job_id: Specific server job ID to join
            wait: Whether to wait for the process to complete

        Returns:
            LaunchResult with process info
        """
        params = RobloxLaunchParams(
            launch_mode="play",
            place_id=place_id,
            game_info=game_info,
            game_instance_id=job_id,
            launch_time=int(time.time() * 1000)
        )

        # Build place launcher URL
        if game_info:
            params.place_launcher_url = (
                f"https://assetgame.roblox.com/game/PlaceLauncher.ashx"
                f"?request=RequestGame&placeId={place_id}"
            )
            if job_id:
                params.place_launcher_url += f"&gameId={job_id}"

        return self.launch_params(params, wait=wait)

    def launch_raw(
        self,
        args: list[str],
        wait: bool = False
    ) -> LaunchResult:
        """
        Launch Roblox with raw command-line arguments.

        Args:
            args: Raw command-line arguments (without the executable)
            wait: Whether to wait for the process to complete

        Returns:
            LaunchResult with process info
        """
        if not self.is_available:
            return LaunchResult(
                success=False,
                error="Roblox player not found. Please install Roblox first."
            )

        full_args = [str(self._player_path)] + args

        logger.info(f"Launching Roblox (raw): {' '.join(full_args)}")

        try:
            if wait:
                result = subprocess.run(full_args, capture_output=True, text=True)
                return LaunchResult(
                    success=result.returncode == 0,
                    player_path=self._player_path,
                    error=result.stderr if result.returncode != 0 else None
                )
            else:
                process = subprocess.Popen(
                    full_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                    if sys.platform == "win32" else 0
                )
                return LaunchResult(
                    success=True,
                    process=process,
                    player_path=self._player_path
                )
        except Exception as e:
            logger.error(f"Failed to launch Roblox: {e}")
            return LaunchResult(
                success=False,
                error=str(e),
                player_path=self._player_path
            )


class RobloxStudioLauncher:
    """
    Roblox Studio launcher.

    Handles launching Roblox Studio for development.
    """

    def __init__(
        self,
        studio_path: Optional[Union[str, Path]] = None,
        version: Optional[str] = None
    ):
        """
        Initialize the Studio launcher.

        Args:
            studio_path: Direct path to RobloxStudioBeta.exe.
                        If None, will auto-detect.
            version: Specific Roblox version to use.
        """
        self._studio_path: Optional[Path] = None
        self._version = version

        if studio_path:
            self._studio_path = Path(studio_path)
        else:
            self._studio_path = find_roblox_studio(version)

    @property
    def studio_path(self) -> Optional[Path]:
        """Get the path to the Roblox Studio executable."""
        return self._studio_path

    @property
    def is_available(self) -> bool:
        """Check if Roblox Studio is available."""
        return self._studio_path is not None and self._studio_path.exists()

    def launch(
        self,
        place_file: Optional[Union[str, Path]] = None,
        wait: bool = False
    ) -> LaunchResult:
        """
        Launch Roblox Studio.

        Args:
            place_file: Optional .rbxl or .rbxlx file to open
            wait: Whether to wait for the process to complete

        Returns:
            LaunchResult with process info
        """
        if not self.is_available:
            return LaunchResult(
                success=False,
                error="Roblox Studio not found. Please install Roblox Studio first."
            )

        args = [str(self._studio_path)]
        if place_file:
            args.append(str(place_file))

        logger.info(f"Launching Roblox Studio: {' '.join(args)}")

        try:
            if wait:
                result = subprocess.run(args, capture_output=True, text=True)
                return LaunchResult(
                    success=result.returncode == 0,
                    player_path=self._studio_path,
                    error=result.stderr if result.returncode != 0 else None
                )
            else:
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                    if sys.platform == "win32" else 0
                )
                return LaunchResult(
                    success=True,
                    process=process,
                    player_path=self._studio_path
                )
        except Exception as e:
            logger.error(f"Failed to launch Roblox Studio: {e}")
            return LaunchResult(
                success=False,
                error=str(e),
                player_path=self._studio_path
            )

    def edit_place(self, place_id: str, wait: bool = False) -> LaunchResult:
        """
        Open a Roblox place for editing in Studio.

        Args:
            place_id: The Roblox place ID to edit
            wait: Whether to wait for the process to complete

        Returns:
            LaunchResult with process info
        """
        if not self.is_available:
            return LaunchResult(
                success=False,
                error="Roblox Studio not found. Please install Roblox Studio first."
            )

        args = [
            str(self._studio_path),
            "-ide",
            f"-placeId={place_id}"
        ]

        logger.info(f"Launching Roblox Studio for place: {place_id}")

        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32" else 0
            )
            return LaunchResult(
                success=True,
                process=process,
                player_path=self._studio_path
            )
        except Exception as e:
            logger.error(f"Failed to launch Roblox Studio: {e}")
            return LaunchResult(
                success=False,
                error=str(e),
                player_path=self._studio_path
            )
