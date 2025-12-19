"""
Roblox Friends API.

Handles friend list with presence (what game they're playing).
"""

from typing import Optional, List
from dataclasses import dataclass

from .http import RobloxHTTP


@dataclass
class FriendPresence:
    """Friend's current presence/status."""
    status: str  # "offline", "online", "ingame", "studio"
    place_id: Optional[int] = None
    universe_id: Optional[int] = None
    job_id: Optional[str] = None
    game_name: Optional[str] = None


@dataclass
class Friend:
    """A friend with their current status."""
    user_id: int
    username: str
    display_name: str
    presence: FriendPresence
    avatar_url: Optional[str] = None
    avatar_bust_url: Optional[str] = None


class RobloxFriends:
    """
    Roblox Friends API.

    Handles friend list with presence data.
    """

    def __init__(self, http: RobloxHTTP):
        self._http = http

    async def get_friends(self, user_id: int, limit: int = 50) -> List[Friend]:
        """
        Get a user's friends with presence data.

        Args:
            user_id: The user ID to get friends for
            limit: Max friends to return

        Returns:
            List of Friend objects with presence
        """
        # Get friends list
        resp = await self._http.get(
            f"https://friends.roblox.com/v1/users/{user_id}/friends"
        )

        if resp.status != 200 or not resp.data:
            return []

        friends_data = resp.data.get("data", [])[:limit]
        if not friends_data:
            return []

        # Get user IDs for presence lookup
        user_ids = [f.get("id") for f in friends_data]

        # Get presence for all friends
        presence_map = await self._get_presences(user_ids)

        # Get avatars
        avatar_map = await self._get_avatars(user_ids)
        bust_map = await self._get_avatar_busts(user_ids)

        # Build friend objects
        friends = []
        for f in friends_data:
            uid = f.get("id")
            presence = presence_map.get(uid, FriendPresence(status="offline"))

            friends.append(Friend(
                user_id=uid,
                username=f.get("name", ""),
                display_name=f.get("displayName", ""),
                presence=presence,
                avatar_url=avatar_map.get(uid),
                avatar_bust_url=bust_map.get(uid),
            ))

        # Sort: in-game first, then online, then offline
        status_order = {"ingame": 0, "studio": 1, "online": 2, "offline": 3}
        friends.sort(key=lambda f: status_order.get(f.presence.status, 4))

        return friends

    async def _get_presences(self, user_ids: List[int]) -> dict:
        """Get presence data for multiple users."""
        if not user_ids:
            return {}

        resp = await self._http.post(
            "https://presence.roblox.com/v1/presence/users",
            data={"userIds": user_ids}
        )

        if resp.status != 200 or not resp.data:
            return {}

        result = {}
        for p in resp.data.get("userPresences", []):
            user_id = p.get("userId")
            presence_type = p.get("userPresenceType", 0)

            # Map presence type to status
            status_map = {
                0: "offline",
                1: "online",
                2: "ingame",
                3: "studio",
            }
            status = status_map.get(presence_type, "offline")

            result[user_id] = FriendPresence(
                status=status,
                place_id=p.get("placeId"),
                universe_id=p.get("universeId"),
                job_id=p.get("gameId"),  # This is actually the job ID
                game_name=p.get("lastLocation"),
            )

        return result

    async def _get_avatars(self, user_ids: List[int]) -> dict:
        """Get headshot avatar URLs for users."""
        if not user_ids:
            return {}

        ids_str = ",".join(str(id) for id in user_ids[:100])
        resp = await self._http.get(
            f"https://thumbnails.roblox.com/v1/users/avatar-headshot"
            f"?userIds={ids_str}&size=100x100&format=Webp&isCircular=false"
        )

        if resp.status != 200 or not resp.data:
            return {}

        result = {}
        for item in resp.data.get("data", []):
            target_id = item.get("targetId")
            if item.get("imageUrl"):
                result[target_id] = item["imageUrl"]

        return result

    async def _get_avatar_busts(self, user_ids: List[int]) -> dict:
        """Get bust avatar URLs for users."""
        if not user_ids:
            return {}

        ids_str = ",".join(str(id) for id in user_ids[:100])
        resp = await self._http.get(
            f"https://thumbnails.roblox.com/v1/users/avatar-bust"
            f"?userIds={ids_str}&size=420x420&format=Webp&isCircular=false"
        )

        if resp.status != 200 or not resp.data:
            return {}

        result = {}
        for item in resp.data.get("data", []):
            target_id = item.get("targetId")
            if item.get("imageUrl"):
                result[target_id] = item["imageUrl"]

        return result

    async def get_friend_count(self, user_id: int) -> int:
        """Get total friend count for a user."""
        resp = await self._http.get(
            f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
        )

        if resp.status != 200 or not resp.data:
            return 0

        return resp.data.get("count", 0)
