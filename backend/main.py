"""
Reblex - A Python Roblox Launcher

Main entry point with pywebview GUI.
"""

import os
import sys
import webview
import asyncio
import threading
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from reblex.client import RobloxClient
from reblex.launcher import RobloxLauncher
from reblex.games import GameInfo, GameServer


def get_cookie_path() -> Path:
    """Get path to stored cookie file."""
    return Path.home() / ".reblex" / "cookie"


def load_cookie() -> str | None:
    """Load cookie from file."""
    path = get_cookie_path()
    if path.exists():
        return path.read_text().strip()
    return None


def save_cookie(cookie: str):
    """Save cookie to file."""
    path = get_cookie_path()
    path.parent.mkdir(exist_ok=True)
    path.write_text(cookie)
    if sys.platform != "win32":
        path.chmod(0o600)


def run_async(coro):
    """Run an async function from sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class Api:
    """
    API bridge between Python backend and JavaScript frontend.

    All methods here are callable from the frontend via:
    window.pywebview.api.methodName(args)
    """

    def __init__(self):
        self._client: RobloxClient | None = None
        self._launcher: RobloxLauncher | None = None
        self._cookie: str | None = load_cookie()

        # Auto-login if we have a saved cookie
        if self._cookie:
            self._init_client()

    def _init_client(self):
        """Initialize the Roblox client with current cookie."""
        if self._cookie:
            self._client = RobloxClient(self._cookie)
            self._launcher = RobloxLauncher(self._client)

    # ============== Auth Methods ==============

    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return self._cookie is not None and self._client is not None

    def login(self, cookie: str) -> dict:
        """
        Login with a .ROBLOSECURITY cookie.

        Returns: {"success": bool, "user": {...} | None, "error": str | None}
        """
        # Clean up cookie
        cookie = cookie.strip()
        if cookie.startswith(".ROBLOSECURITY="):
            cookie = cookie[15:]

        # Try to authenticate
        self._cookie = cookie
        self._init_client()

        async def do_login():
            try:
                user = await self._client.get_user()
                if user:
                    save_cookie(cookie)
                    return {
                        "success": True,
                        "user": {
                            "id": user.user_id,
                            "username": user.username,
                            "displayName": user.display_name,
                        },
                        "error": None
                    }
                else:
                    self._cookie = None
                    self._client = None
                    return {
                        "success": False,
                        "user": None,
                        "error": "Invalid cookie"
                    }
            except Exception as e:
                self._cookie = None
                self._client = None
                return {
                    "success": False,
                    "user": None,
                    "error": str(e)
                }

        return run_async(do_login())

    def logout(self):
        """Logout and clear saved cookie."""
        self._cookie = None
        self._client = None
        self._launcher = None

        path = get_cookie_path()
        if path.exists():
            path.unlink()

    def get_current_user(self) -> dict | None:
        """Get current logged in user info."""
        if not self._client:
            return None

        async def fetch():
            try:
                user = await self._client.get_user()
                if user:
                    return {
                        "id": user.user_id,
                        "username": user.username,
                        "displayName": user.display_name,
                    }
            except:
                pass
            return None

        return run_async(fetch())

    # ============== Game Methods ==============

    def get_game_info(self, place_id: int) -> dict | None:
        """Get information about a game."""
        if not self._client:
            return None

        async def fetch():
            try:
                game = await self._client.get_game_info(place_id)
                if game:
                    return {
                        "universeId": game.universe_id,
                        "placeId": game.place_id,
                        "name": game.name,
                        "description": game.description,
                        "creatorName": game.creator_name,
                        "creatorType": game.creator_type,
                        "playing": game.playing,
                        "visits": game.visits,
                        "maxPlayers": game.max_players,
                        "favorites": game.favorites,
                        "genre": game.genre,
                    }
            except:
                pass
            return None

        return run_async(fetch())

    def get_servers(self, place_id: int, limit: int = 10) -> list:
        """Get list of servers for a game."""
        if not self._client:
            return []

        async def fetch():
            try:
                servers = await self._client.get_servers(place_id, limit=limit)
                return [
                    {
                        "jobId": s.job_id,
                        "playing": s.playing,
                        "maxPlayers": s.max_players,
                        "ping": s.ping,
                        "fps": s.fps,
                    }
                    for s in servers
                ]
            except:
                pass
            return []

        return run_async(fetch())

    def launch_game(self, place_id: int, job_id: str | None = None) -> dict:
        """
        Launch a Roblox game.

        Returns: {"success": bool, "message": str}
        """
        if not self._client or not self._launcher:
            return {"success": False, "message": "Not logged in"}

        async def do_launch():
            try:
                result = await self._launcher.launch(place_id, job_id=job_id)
                return {
                    "success": result.success,
                    "message": result.message
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": str(e)
                }

        return run_async(do_launch())

    # ============== Utility Methods ==============

    def get_roblox_path(self) -> str | None:
        """Get path to Roblox player executable."""
        path = RobloxLauncher.find_roblox_player()
        return str(path) if path else None

    def is_roblox_installed(self) -> bool:
        """Check if Roblox is installed."""
        return RobloxLauncher.find_roblox_player() is not None


def get_frontend_url() -> str:
    """Get the URL for the frontend."""
    # Check if running in development mode
    if os.environ.get("DEV"):
        return "http://localhost:5173"

    # Production: load from built files
    frontend_path = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
    if frontend_path.exists():
        return f"file://{frontend_path}"

    # Fallback: try relative path
    return "frontend/dist/index.html"


def main():
    """Main entry point."""
    api = Api()

    # Check if dev mode
    is_dev = os.environ.get("DEV", "").lower() in ("1", "true", "yes")

    if is_dev:
        url = "http://localhost:5173"
    else:
        # Look for built frontend
        dist_path = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
        if dist_path.exists():
            url = str(dist_path)
        else:
            print("Error: Frontend not built. Run 'npm run build' in frontend folder.")
            print("Or set DEV=1 and run 'npm run dev' for development.")
            sys.exit(1)

    window = webview.create_window(
        title="Reblex",
        url=url,
        js_api=api,
        width=1000,
        height=700,
        min_size=(800, 600),
        background_color="#0f0f0f",
    )

    webview.start(debug=is_dev)


if __name__ == "__main__":
    main()
