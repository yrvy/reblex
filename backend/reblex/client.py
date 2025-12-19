"""
Main Roblox client that wraps all services.
"""

from typing import Optional

from .http import RobloxHTTP
from .auth import RobloxAuth, AuthenticatedUser
from .games import RobloxGames, GameInfo, GameServer


class RobloxClient:
    """
    Main Roblox API client.

    Provides access to all Roblox services through a single interface.

    Example:
        async with RobloxClient(cookie) as client:
            user = await client.get_user()
            print(f"Logged in as {user.username}")

            servers = await client.get_servers(place_id)
            for server in servers:
                print(f"Server {server.job_id}: {server.playing} players")
    """

    def __init__(self, cookie: Optional[str] = None):
        """
        Initialize the Roblox client.

        Args:
            cookie: The .ROBLOSECURITY cookie value
        """
        self._http = RobloxHTTP(cookie)
        self._auth = RobloxAuth(self._http)
        self._games = RobloxGames(self._http)
        self._user: Optional[AuthenticatedUser] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the client and release resources."""
        await self._http.close()

    @property
    def auth(self) -> RobloxAuth:
        """Access the authentication service."""
        return self._auth

    @property
    def games(self) -> RobloxGames:
        """Access the games service."""
        return self._games

    def set_cookie(self, cookie: str):
        """Set the authentication cookie."""
        self._http.cookie = cookie
        self._user = None

    # Convenience methods

    async def get_user(self) -> Optional[AuthenticatedUser]:
        """Get the authenticated user."""
        if not self._user:
            self._user = await self._auth.get_authenticated_user()
        return self._user

    async def validate(self) -> bool:
        """Validate that the client is authenticated."""
        return await self._auth.validate_cookie()

    async def get_auth_ticket(self) -> Optional[str]:
        """Get an authentication ticket for game launching."""
        return await self._auth.get_authentication_ticket()

    async def get_game_info(self, place_id: int) -> Optional[GameInfo]:
        """Get information about a game."""
        return await self._games.get_game_info_by_place(place_id)

    async def get_servers(
        self,
        place_id: int,
        limit: int = 10,
    ) -> list[GameServer]:
        """Get available servers for a game."""
        servers, _ = await self._games.get_servers(place_id, limit=limit)
        return servers

    async def join_game(
        self,
        place_id: int,
        job_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Request to join a game.

        Returns the join response which contains connection info.
        """
        return await self._games.join_game(place_id, job_id)
