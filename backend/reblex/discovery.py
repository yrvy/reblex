"""
Roblox Discovery API for home feed content.

Handles recommendations, recently played (continue), and favorites.
"""

from typing import Optional, List
from dataclasses import dataclass, field

from .http import RobloxHTTP


@dataclass
class HomeGame:
    """A game shown on the home page."""
    universe_id: int
    place_id: int
    name: str
    player_count: int
    total_upvotes: int
    total_downvotes: int
    thumbnail_url: Optional[str] = None
    icon_url: Optional[str] = None


class RobloxDiscovery:
    """
    Roblox Discovery API.

    Handles home page content like recommendations, recently played, and favorites.
    """

    def __init__(self, http: RobloxHTTP):
        self._http = http

    async def get_home_recommendations(self) -> List[HomeGame]:
        """Get recommended games for home page."""
        return await self._get_omni_recommendation("GameHomePage")

    async def get_continue_playing(self) -> List[HomeGame]:
        """Get recently played games (continue/jump back in)."""
        return await self._get_omni_recommendation("ContinuePlaying")

    async def get_favorites(self) -> List[HomeGame]:
        """Get user's favorite games."""
        return await self._get_omni_recommendation("Favorites")

    async def _get_omni_recommendation(self, page_type: str) -> List[HomeGame]:
        """
        Get games from the omni-recommendation API.

        Args:
            page_type: "GameHomePage", "ContinuePlaying", or "Favorites"
        """
        resp = await self._http.post(
            "https://apis.roblox.com/discovery-api/omni-recommendation",
            data={
                "pageType": page_type,
                "sessionId": "reblex",
            }
        )

        if resp.status != 200 or not resp.data:
            return []

        games = []
        sorts = resp.data.get("sorts", [])

        for sort in sorts:
            for rec in sort.get("recommendationList", []):
                content_type = rec.get("contentType")
                content_id = rec.get("contentId")

                if content_type == "Game" and content_id:
                    games.append(HomeGame(
                        universe_id=int(content_id),
                        place_id=0,  # Will be filled in by get_universe_details
                        name="",
                        player_count=0,
                        total_upvotes=0,
                        total_downvotes=0,
                    ))

        # Get full details for these universes
        if games:
            universe_ids = [g.universe_id for g in games]
            details = await self._get_universe_details(universe_ids)
            votes = await self._get_universe_votes(universe_ids)
            thumbnails = await self._get_universe_thumbnails(universe_ids)
            icons = await self._get_universe_icons(universe_ids)

            # Merge details
            for game in games:
                if game.universe_id in details:
                    d = details[game.universe_id]
                    game.place_id = d.get("rootPlaceId", 0)
                    game.name = d.get("name", "")
                    game.player_count = d.get("playing", 0)

                if game.universe_id in votes:
                    v = votes[game.universe_id]
                    game.total_upvotes = v.get("upVotes", 0)
                    game.total_downvotes = v.get("downVotes", 0)

                if game.universe_id in thumbnails:
                    game.thumbnail_url = thumbnails[game.universe_id]

                if game.universe_id in icons:
                    game.icon_url = icons[game.universe_id]

        return games

    async def _get_universe_details(self, universe_ids: List[int]) -> dict:
        """Get details for multiple universes."""
        if not universe_ids:
            return {}

        # API accepts max 50 at a time
        ids_str = ",".join(str(id) for id in universe_ids[:50])
        resp = await self._http.get(
            f"https://games.roblox.com/v1/games?universeIds={ids_str}"
        )

        if resp.status != 200 or not resp.data:
            return {}

        result = {}
        for game in resp.data.get("data", []):
            result[game.get("id")] = game

        return result

    async def _get_universe_votes(self, universe_ids: List[int]) -> dict:
        """Get vote counts for universes."""
        if not universe_ids:
            return {}

        ids_str = ",".join(str(id) for id in universe_ids[:50])
        resp = await self._http.get(
            f"https://games.roblox.com/v1/games/votes?universeIds={ids_str}"
        )

        if resp.status != 200 or not resp.data:
            return {}

        result = {}
        for vote in resp.data.get("data", []):
            result[vote.get("id")] = vote

        return result

    async def _get_universe_thumbnails(self, universe_ids: List[int]) -> dict:
        """Get thumbnail URLs for universes."""
        if not universe_ids:
            return {}

        ids_str = ",".join(str(id) for id in universe_ids[:50])
        resp = await self._http.get(
            f"https://thumbnails.roblox.com/v1/games/multiget/thumbnails"
            f"?universeIds={ids_str}&size=384x216&format=Webp&isCircular=false"
        )

        if resp.status != 200 or not resp.data:
            return {}

        result = {}
        for item in resp.data.get("data", []):
            universe_id = item.get("universeId")
            thumbnails = item.get("thumbnails", [])
            if thumbnails and thumbnails[0].get("imageUrl"):
                result[universe_id] = thumbnails[0]["imageUrl"]

        return result

    async def _get_universe_icons(self, universe_ids: List[int]) -> dict:
        """Get icon URLs for universes."""
        if not universe_ids:
            return {}

        ids_str = ",".join(str(id) for id in universe_ids[:50])
        resp = await self._http.get(
            f"https://thumbnails.roblox.com/v1/games/icons"
            f"?universeIds={ids_str}&size=150x150&format=Webp&isCircular=false"
        )

        if resp.status != 200 or not resp.data:
            return {}

        result = {}
        for item in resp.data.get("data", []):
            target_id = item.get("targetId")
            if item.get("imageUrl"):
                result[target_id] = item["imageUrl"]

        return result

    async def search_games(self, query: str, limit: int = 12) -> List[HomeGame]:
        """Search for games."""
        resp = await self._http.get(
            f"https://apis.roblox.com/search-api/omni-search"
            f"?searchQuery={query}&pageToken=&sessionId=reblex"
        )

        if resp.status != 200 or not resp.data:
            return []

        games = []
        for item in resp.data.get("searchResults", []):
            if item.get("contentType") == "Game":
                universe_id = item.get("universeId")
                if universe_id:
                    games.append(HomeGame(
                        universe_id=universe_id,
                        place_id=item.get("rootPlaceId", 0),
                        name=item.get("name", ""),
                        player_count=item.get("playerCount", 0),
                        total_upvotes=item.get("totalUpVotes", 0),
                        total_downvotes=item.get("totalDownVotes", 0),
                    ))

        # Get thumbnails
        if games:
            universe_ids = [g.universe_id for g in games[:limit]]
            thumbnails = await self._get_universe_thumbnails(universe_ids)
            for game in games:
                if game.universe_id in thumbnails:
                    game.thumbnail_url = thumbnails[game.universe_id]

        return games[:limit]
