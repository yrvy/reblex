#!/usr/bin/env python3
"""
Reblex - A Python Roblox Launcher

Main entry point for the Roblox launcher.

Usage:
    python main.py                          # Show help
    python main.py <roblox-player://url>    # Launch from URL
    python main.py --place <place_id>       # Launch a place directly
    python main.py --register               # Register as protocol handler
    python main.py --unregister             # Unregister protocol handler
    python main.py --info                   # Show Roblox installation info
"""

import argparse
import sys
import logging
from pathlib import Path

from roblox_launcher import RobloxLauncher, parse_roblox_url, find_roblox_player
from roblox_launcher.launcher import RobloxStudioLauncher
from roblox_launcher.finder import get_installed_versions
from roblox_launcher.register import (
    register_protocol_handler,
    unregister_protocol_handler,
    is_protocol_registered,
    get_registered_handler
)


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def show_info():
    """Display Roblox installation information."""
    print("Reblex - Roblox Launcher")
    print("=" * 40)

    # Check protocol registration
    if is_protocol_registered():
        handler = get_registered_handler()
        print(f"\nProtocol handler: Registered")
        print(f"Handler: {handler}")
    else:
        print(f"\nProtocol handler: Not registered")

    # Find Roblox player
    player_path = find_roblox_player()
    if player_path:
        print(f"\nRoblox Player: {player_path}")
    else:
        print("\nRoblox Player: Not found")

    # List installed versions
    versions = get_installed_versions()
    if versions:
        print(f"\nInstalled versions ({len(versions)}):")
        for v in versions:
            features = []
            if v["has_player"]:
                features.append("Player")
            if v["has_studio"]:
                features.append("Studio")
            print(f"  - {v['version']} ({', '.join(features)})")
    else:
        print("\nNo Roblox versions found")


def launch_url(url: str, verbose: bool = False):
    """Launch Roblox from a protocol URL."""
    launcher = RobloxLauncher()

    if not launcher.is_available:
        print("Error: Roblox is not installed or could not be found.")
        print("Please install Roblox from https://www.roblox.com")
        sys.exit(1)

    print(f"Launching Roblox...")
    if verbose:
        params = parse_roblox_url(url)
        print(f"Launch mode: {params.launch_mode}")
        print(f"Place launcher URL: {params.place_launcher_url}")

    result = launcher.launch_url(url)

    if result.success:
        print("Roblox launched successfully!")
        if verbose:
            print(f"Player path: {result.player_path}")
    else:
        print(f"Failed to launch Roblox: {result.error}")
        sys.exit(1)


def launch_place(place_id: str, verbose: bool = False):
    """Launch a specific Roblox place."""
    launcher = RobloxLauncher()

    if not launcher.is_available:
        print("Error: Roblox is not installed or could not be found.")
        sys.exit(1)

    print(f"Launching place {place_id}...")

    result = launcher.launch_place(place_id)

    if result.success:
        print("Roblox launched successfully!")
    else:
        print(f"Failed to launch Roblox: {result.error}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reblex - A Python Roblox Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "roblox-player:1+launchmode:play+..."
  %(prog)s --place 123456789
  %(prog)s --register
  %(prog)s --info
        """
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="roblox-player:// URL to launch"
    )

    parser.add_argument(
        "--place", "-p",
        metavar="ID",
        help="Launch a specific place by ID"
    )

    parser.add_argument(
        "--register",
        action="store_true",
        help="Register as the roblox-player:// protocol handler"
    )

    parser.add_argument(
        "--unregister",
        action="store_true",
        help="Unregister as the protocol handler"
    )

    parser.add_argument(
        "--info", "-i",
        action="store_true",
        help="Show Roblox installation information"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Handle commands
    if args.register:
        if register_protocol_handler():
            print("Successfully registered as protocol handler")
        else:
            print("Failed to register protocol handler")
            sys.exit(1)
        return

    if args.unregister:
        if unregister_protocol_handler():
            print("Successfully unregistered protocol handler")
        else:
            print("Failed to unregister protocol handler")
            sys.exit(1)
        return

    if args.info:
        show_info()
        return

    if args.place:
        launch_place(args.place, args.verbose)
        return

    if args.url:
        launch_url(args.url, args.verbose)
        return

    # No arguments - show help
    parser.print_help()


if __name__ == "__main__":
    main()
