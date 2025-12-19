"""
Reblex - A Python Roblox Launcher

Main entry point with pywebview GUI.
"""

import os
import sys
import webview
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from reblex.client import RobloxClient
from reblex.launcher import RobloxLauncher


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


class Api:
    """
    API bridge between Python backend and JavaScript frontend.

    All methods here are callable from the frontend via:
    window.pywebview.api.methodName(args)
    """

    def __init__(self):
        self._cookie: str | None = load_cookie()
        self._user_id: int | None = None

    # ============== Auth Methods ==============

    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return self._cookie is not None

    def login(self, cookie: str) -> dict:
        """Login with a .ROBLOSECURITY cookie."""
        cookie = cookie.strip()
        if cookie.startswith(".ROBLOSECURITY="):
            cookie = cookie[15:]

        async def do_login():
            async with RobloxClient(cookie) as client:
                try:
                    user = await client.get_user()
                    if user:
                        self._cookie = cookie
                        self._user_id = user.user_id
                        save_cookie(cookie)
                        avatar = await client.get_user_headshot(user.user_id)
                        return {
                            "success": True,
                            "user": {
                                "id": user.user_id,
                                "username": user.username,
                                "displayName": user.display_name,
                                "avatar": avatar,
                            },
                            "error": None
                        }
                    else:
                        return {"success": False, "user": None, "error": "Invalid cookie"}
                except Exception as e:
                    return {"success": False, "user": None, "error": str(e)}

        return asyncio.run(do_login())

    def logout(self):
        """Logout and clear saved cookie."""
        self._cookie = None
        self._user_id = None

        path = get_cookie_path()
        if path.exists():
            path.unlink()

    def get_current_user(self) -> dict | None:
        """Get current logged in user info."""
        if not self._cookie:
            return None

        async def fetch():
            async with RobloxClient(self._cookie) as client:
                try:
                    user = await client.get_user()
                    if user:
                        self._user_id = user.user_id
                        avatar = await client.get_user_headshot(user.user_id)
                        return {
                            "id": user.user_id,
                            "username": user.username,
                            "displayName": user.display_name,
                            "avatar": avatar,
                        }
                except:
                    pass
                return None

        return asyncio.run(fetch())

    # ============== Home Feed Methods ==============

    def get_home_feed(self) -> dict:
        """Get the home page feed with recommendations, continue, favorites."""
        if not self._cookie:
            return {"friends": [], "continue": [], "favorites": []}

        async def fetch():
            async with RobloxClient(self._cookie) as client:
                try:
                    # Get user ID if we don't have it
                    if not self._user_id:
                        user = await client.get_user()
                        if user:
                            self._user_id = user.user_id

                    continue_games = await client.discovery.get_continue_playing()
                    favorites = await client.discovery.get_favorites()
                    friends = []

                    if self._user_id:
                        friends = await client.friends.get_friends(self._user_id, limit=20)

                    return {
                        "friends": [
                            {
                                "id": f.user_id,
                                "username": f.username,
                                "displayName": f.display_name,
                                "avatar": f.avatar_url,
                                "status": f.presence.status,
                                "gameName": f.presence.game_name,
                                "placeId": f.presence.place_id,
                                "jobId": f.presence.job_id,
                            }
                            for f in friends
                        ],
                        "continue": [
                            {
                                "universeId": g.universe_id,
                                "placeId": g.place_id,
                                "name": g.name,
                                "playerCount": g.player_count,
                                "upvotes": g.total_upvotes,
                                "downvotes": g.total_downvotes,
                                "thumbnail": g.thumbnail_url,
                                "icon": g.icon_url,
                            }
                            for g in continue_games[:6]
                        ],
                        "favorites": [
                            {
                                "universeId": g.universe_id,
                                "placeId": g.place_id,
                                "name": g.name,
                                "playerCount": g.player_count,
                                "upvotes": g.total_upvotes,
                                "downvotes": g.total_downvotes,
                                "thumbnail": g.thumbnail_url,
                                "icon": g.icon_url,
                            }
                            for g in favorites[:6]
                        ],
                    }
                except Exception as e:
                    print(f"Error fetching home feed: {e}")
                    import traceback
                    traceback.print_exc()
                    return {"friends": [], "continue": [], "favorites": [], "error": str(e)}

        return asyncio.run(fetch())

    def get_friends(self, limit: int = 20) -> list:
        """Get friends with presence."""
        if not self._cookie or not self._user_id:
            return []

        async def fetch():
            async with RobloxClient(self._cookie) as client:
                try:
                    friends = await client.friends.get_friends(self._user_id, limit=limit)
                    return [
                        {
                            "id": f.user_id,
                            "username": f.username,
                            "displayName": f.display_name,
                            "avatar": f.avatar_url,
                            "status": f.presence.status,
                            "gameName": f.presence.game_name,
                            "placeId": f.presence.place_id,
                            "jobId": f.presence.job_id,
                        }
                        for f in friends
                    ]
                except:
                    return []

        return asyncio.run(fetch())

    def search_games(self, query: str) -> list:
        """Search for games."""
        if not self._cookie:
            return []

        async def fetch():
            async with RobloxClient(self._cookie) as client:
                try:
                    games = await client.discovery.search_games(query, limit=12)
                    return [
                        {
                            "universeId": g.universe_id,
                            "placeId": g.place_id,
                            "name": g.name,
                            "playerCount": g.player_count,
                            "upvotes": g.total_upvotes,
                            "downvotes": g.total_downvotes,
                            "thumbnail": g.thumbnail_url,
                        }
                        for g in games
                    ]
                except:
                    return []

        return asyncio.run(fetch())

    # ============== Game Methods ==============

    def get_game_info(self, place_id: int) -> dict | None:
        """Get information about a game."""
        if not self._cookie:
            return None

        async def fetch():
            async with RobloxClient(self._cookie) as client:
                try:
                    game = await client.get_game_info(place_id)
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

        return asyncio.run(fetch())

    def get_servers(self, place_id: int, limit: int = 10) -> list:
        """Get list of servers for a game."""
        if not self._cookie:
            return []

        async def fetch():
            async with RobloxClient(self._cookie) as client:
                try:
                    servers = await client.get_servers(place_id, limit=limit)
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
                    return []

        return asyncio.run(fetch())

    def launch_game(self, place_id: int, job_id: str | None = None) -> dict:
        """Launch a Roblox game."""
        if not self._cookie:
            return {"success": False, "message": "Not logged in"}

        async def do_launch():
            async with RobloxClient(self._cookie) as client:
                try:
                    launcher = RobloxLauncher(client)
                    result = await launcher.launch(place_id, job_id=job_id)
                    return {"success": result.success, "message": result.message}
                except Exception as e:
                    return {"success": False, "message": str(e)}

        return asyncio.run(do_launch())

    # ============== Utility Methods ==============

    def is_roblox_installed(self) -> bool:
        """Check if Roblox is installed."""
        return RobloxLauncher.find_roblox_player() is not None


def main():
    """Main entry point."""
    api = Api()

    is_dev = os.environ.get("DEV", "").lower() in ("1", "true", "yes")

    if is_dev:
        url = "http://localhost:5173"
    else:
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
        width=1200,
        height=800,
        min_size=(900, 600),
        background_color="#0f0f0f",
    )

    webview.start(debug=is_dev)


if __name__ == "__main__":
    main()
