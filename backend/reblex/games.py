"""
Roblox game services.

Handles game information retrieval, server browsing, and game joining.
"""

from typing import Optional, List
from dataclasses import dataclass, field
import uuid

from .http import RobloxHTTP


@dataclass
class GameInfo:
    """Information about a Roblox game."""
    universe_id: int
    place_id: int
    name: str
    description: str
    creator_name: str
    creator_type: str  # "User" or "Group"
    creator_id: int
    playing: int
    visits: int
    max_players: int
    favorites: int
    genre: str


@dataclass
class GameServer:
    """Information about a game server instance."""
    job_id: str  # Server instance ID
    playing: int
    max_players: int
    player_tokens: List[str] = field(default_factory=list)
    fps: float = 0.0
    ping: int = 0


@dataclass
class JoinInfo:
    """Information needed to join a game."""
    join_script_url: str
    auth_ticket: str
    place_id: int
    job_id: Optional[str] = None


class RobloxGames:
    """
    Roblox games service.

    Handles:
    - Fetching game details
    - Browsing servers
    - Getting join information
    """

    def __init__(self, http: RobloxHTTP):
        self._http = http

    async def get_universe_id(self, place_id: int) -> Optional[int]:
        """
        Get the universe ID for a place.

        Args:
            place_id: The place ID

        Returns:
            Universe ID or None
        """
        resp = await self._http.get(
            f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
        )

        if resp.status != 200 or not resp.data:
            return None

        return resp.data.get("universeId")

    async def get_game_info(self, universe_id: int) -> Optional[GameInfo]:
        """
        Get detailed game information.

        Args:
            universe_id: The universe ID

        Returns:
            GameInfo or None
        """
        resp = await self._http.get(
            f"https://games.roblox.com/v1/games?universeIds={universe_id}"
        )

        if resp.status != 200 or not resp.data:
            return None

        games = resp.data.get("data", [])
        if not games:
            return None

        game = games[0]
        return GameInfo(
            universe_id=game.get("id"),
            place_id=game.get("rootPlaceId"),
            name=game.get("name", ""),
            description=game.get("description", ""),
            creator_name=game.get("creator", {}).get("name", ""),
            creator_type=game.get("creator", {}).get("type", ""),
            creator_id=game.get("creator", {}).get("id", 0),
            playing=game.get("playing", 0),
            visits=game.get("visits", 0),
            max_players=game.get("maxPlayers", 0),
            favorites=game.get("favoritedCount", 0),
            genre=game.get("genre", ""),
        )

    async def get_game_info_by_place(self, place_id: int) -> Optional[GameInfo]:
        """
        Get game information by place ID.

        Args:
            place_id: The place ID

        Returns:
            GameInfo or None
        """
        universe_id = await self.get_universe_id(place_id)
        if not universe_id:
            return None
        return await self.get_game_info(universe_id)

    async def get_servers(
        self,
        place_id: int,
        server_type: str = "Public",
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> tuple[List[GameServer], Optional[str]]:
        """
        Get available game servers.

        Args:
            place_id: The place ID
            server_type: "Public", "Friend", or "VIP"
            limit: Max servers to return (10, 25, 50, 100)
            cursor: Pagination cursor

        Returns:
            Tuple of (list of GameServer, next cursor or None)
        """
        url = f"https://games.roblox.com/v1/games/{place_id}/servers/{server_type}"
        url += f"?limit={limit}"
        if cursor:
            url += f"&cursor={cursor}"

        resp = await self._http.get(url)

        if resp.status != 200 or not resp.data:
            return [], None

        servers = []
        for srv in resp.data.get("data", []):
            servers.append(GameServer(
                job_id=srv.get("id", ""),
                playing=srv.get("playing", 0),
                max_players=srv.get("maxPlayers", 0),
                player_tokens=srv.get("playerTokens", []),
                fps=srv.get("fps", 0.0),
                ping=srv.get("ping", 0),
            ))

        next_cursor = resp.data.get("nextPageCursor")
        return servers, next_cursor

    async def join_game(
        self,
        place_id: int,
        job_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Request to join a game.

        Args:
            place_id: The place ID to join
            job_id: Specific server instance ID (optional)

        Returns:
            Join response data or None
        """
        # Generate a unique join attempt ID
        join_attempt_id = str(uuid.uuid4())

        data = {
            "placeId": place_id,
            "isTeleport": False,
            "joinAttemptId": join_attempt_id,
            "joinAttemptOrigin": "PlayButton",
        }

        if job_id:
            # Join specific server
            data["gameId"] = job_id
            url = "https://gamejoin.roblox.com/v1/join-game-instance"
        else:
            # Join any server
            url = "https://gamejoin.roblox.com/v1/join-game"

        resp = await self._http.post(url, data=data)

        if resp.status != 200:
            return None

        return resp.data

    async def join_private_server(
        self,
        place_id: int,
        access_code: str,
    ) -> Optional[dict]:
        """
        Join a private/VIP server.

        Args:
            place_id: The place ID
            access_code: Private server access code

        Returns:
            Join response data or None
        """
        join_attempt_id = str(uuid.uuid4())

        data = {
            "placeId": place_id,
            "accessCode": access_code,
            "isTeleport": False,
            "joinAttemptId": join_attempt_id,
            "joinAttemptOrigin": "PrivateServerJoin",
        }

        resp = await self._http.post(
            "https://gamejoin.roblox.com/v1/join-private-game",
            data=data
        )

        if resp.status != 200:
            return None

        return resp.data

    async def get_game_thumbnail(
        self,
        universe_id: int,
        size: str = "768x432",
    ) -> Optional[str]:
        """
        Get a game's thumbnail URL.

        Args:
            universe_id: The universe ID
            size: Image size (e.g., "768x432", "512x512")

        Returns:
            Thumbnail URL or None
        """
        resp = await self._http.get(
            f"https://thumbnails.roblox.com/v1/games/icons"
            f"?universeIds={universe_id}&size={size}&format=Png"
        )

        if resp.status != 200 or not resp.data:
            return None

        data = resp.data.get("data", [])
        if not data:
            return None

        return data[0].get("imageUrl")
