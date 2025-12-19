"""
Command-line interface for Reblex.
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

from .client import RobloxClient
from .launcher import RobloxLauncher


def get_cookie_from_env() -> str | None:
    """Get cookie from environment variable."""
    return os.environ.get("ROBLOSECURITY")


def get_cookie_from_file() -> str | None:
    """Get cookie from ~/.reblex/cookie file."""
    cookie_file = Path.home() / ".reblex" / "cookie"
    if cookie_file.exists():
        return cookie_file.read_text().strip()
    return None


def save_cookie_to_file(cookie: str):
    """Save cookie to ~/.reblex/cookie file."""
    reblex_dir = Path.home() / ".reblex"
    reblex_dir.mkdir(exist_ok=True)

    cookie_file = reblex_dir / "cookie"
    cookie_file.write_text(cookie)
    # Set restrictive permissions
    if sys.platform != "win32":
        cookie_file.chmod(0o600)


def get_cookie(args) -> str | None:
    """Get cookie from args, env, or file."""
    if args.cookie:
        return args.cookie
    return get_cookie_from_env() or get_cookie_from_file()


async def cmd_login(args):
    """Handle the login command."""
    cookie = args.cookie

    if not cookie:
        print("Enter your .ROBLOSECURITY cookie:")
        cookie = input().strip()

    if not cookie:
        print("Error: No cookie provided")
        return 1

    # Clean up cookie if it has the full format
    if cookie.startswith(".ROBLOSECURITY="):
        cookie = cookie[15:]
    if cookie.startswith("_|WARNING:-"):
        # Extract just the cookie value
        parts = cookie.split("|_")
        if len(parts) >= 2:
            cookie = parts[-1]

    async with RobloxClient(cookie) as client:
        user = await client.get_user()

        if not user:
            print("Error: Invalid cookie or authentication failed")
            return 1

        save_cookie_to_file(cookie)
        print(f"Logged in as: {user.display_name} (@{user.username})")
        print(f"User ID: {user.user_id}")
        print("Cookie saved to ~/.reblex/cookie")

    return 0


async def cmd_whoami(args):
    """Handle the whoami command."""
    cookie = get_cookie(args)
    if not cookie:
        print("Error: Not logged in. Run 'reblex login' first.")
        return 1

    async with RobloxClient(cookie) as client:
        user = await client.get_user()

        if not user:
            print("Error: Invalid cookie or session expired")
            return 1

        print(f"Display Name: {user.display_name}")
        print(f"Username: @{user.username}")
        print(f"User ID: {user.user_id}")

    return 0


async def cmd_info(args):
    """Handle the info command."""
    place_id = args.place_id

    cookie = get_cookie(args)
    async with RobloxClient(cookie) as client:
        game = await client.get_game_info(place_id)

        if not game:
            print(f"Error: Could not find game with place ID {place_id}")
            return 1

        print(f"Name: {game.name}")
        print(f"Place ID: {game.place_id}")
        print(f"Universe ID: {game.universe_id}")
        print(f"Creator: {game.creator_name} ({game.creator_type})")
        print(f"Playing: {game.playing:,}")
        print(f"Visits: {game.visits:,}")
        print(f"Favorites: {game.favorites:,}")
        print(f"Max Players: {game.max_players}")
        print(f"Genre: {game.genre}")

    return 0


async def cmd_servers(args):
    """Handle the servers command."""
    place_id = args.place_id
    limit = args.limit

    cookie = get_cookie(args)
    async with RobloxClient(cookie) as client:
        servers = await client.get_servers(place_id, limit=limit)

        if not servers:
            print("No servers available")
            return 0

        print(f"{'#':<4} {'Players':<12} {'Job ID':<40}")
        print("-" * 60)

        for i, server in enumerate(servers):
            print(f"{i:<4} {server.playing}/{server.max_players:<10} {server.job_id}")

    return 0


async def cmd_launch(args):
    """Handle the launch command."""
    place_id = args.place_id
    job_id = args.server

    cookie = get_cookie(args)
    if not cookie:
        print("Error: Not logged in. Run 'reblex login' first.")
        return 1

    async with RobloxClient(cookie) as client:
        # Show what we're joining
        game = await client.get_game_info(place_id)
        if game:
            print(f"Game: {game.name}")
            print(f"Players: {game.playing:,}")

        launcher = RobloxLauncher(client)

        if not launcher.is_installed:
            print("Warning: Roblox installation not found. Trying protocol handler...")

        if job_id:
            print(f"Joining server: {job_id}")
            result = await launcher.launch(place_id, job_id=job_id)
        else:
            print("Joining game...")
            result = await launcher.launch(place_id)

        if result.success:
            print(f"✓ {result.message}")
        else:
            print(f"✗ {result.message}")
            return 1

    return 0


async def cmd_join_server(args):
    """Handle the join-server command."""
    place_id = args.place_id
    server_index = args.index

    cookie = get_cookie(args)
    if not cookie:
        print("Error: Not logged in. Run 'reblex login' first.")
        return 1

    async with RobloxClient(cookie) as client:
        launcher = RobloxLauncher(client)

        # Get servers first
        servers = await client.get_servers(place_id, limit=server_index + 1)

        if not servers:
            print("No servers available")
            return 1

        if server_index >= len(servers):
            print(f"Server index {server_index} not available (max: {len(servers) - 1})")
            return 1

        server = servers[server_index]
        print(f"Joining server #{server_index}: {server.playing}/{server.max_players} players")

        result = await launcher.launch(place_id, job_id=server.job_id)

        if result.success:
            print(f"✓ {result.message}")
        else:
            print(f"✗ {result.message}")
            return 1

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="reblex",
        description="Reblex - A Python Roblox Launcher",
    )
    parser.add_argument(
        "--cookie", "-c",
        help="Override .ROBLOSECURITY cookie"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # login
    login_parser = subparsers.add_parser("login", help="Login with cookie")
    login_parser.add_argument("cookie", nargs="?", help="The .ROBLOSECURITY cookie")

    # whoami
    subparsers.add_parser("whoami", help="Show current user")

    # info
    info_parser = subparsers.add_parser("info", help="Get game information")
    info_parser.add_argument("place_id", type=int, help="Place ID")

    # servers
    servers_parser = subparsers.add_parser("servers", help="List game servers")
    servers_parser.add_argument("place_id", type=int, help="Place ID")
    servers_parser.add_argument("--limit", "-n", type=int, default=10, help="Max servers")

    # launch
    launch_parser = subparsers.add_parser("launch", help="Launch a game")
    launch_parser.add_argument("place_id", type=int, help="Place ID")
    launch_parser.add_argument("--server", "-s", help="Specific server Job ID")

    # join-server
    join_parser = subparsers.add_parser("join-server", help="Join specific server by index")
    join_parser.add_argument("place_id", type=int, help="Place ID")
    join_parser.add_argument("index", type=int, help="Server index (0 = first)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Map commands to handlers
    handlers = {
        "login": cmd_login,
        "whoami": cmd_whoami,
        "info": cmd_info,
        "servers": cmd_servers,
        "launch": cmd_launch,
        "join-server": cmd_join_server,
    }

    handler = handlers.get(args.command)
    if handler:
        return asyncio.run(handler(args))

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
