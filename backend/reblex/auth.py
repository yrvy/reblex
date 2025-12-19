"""
Roblox authentication services.

Handles CSRF tokens, authentication tickets, and user validation.
"""

from typing import Optional
from dataclasses import dataclass

from .http import RobloxHTTP


@dataclass
class AuthenticatedUser:
    """Information about the authenticated user."""
    user_id: int
    username: str
    display_name: str


class RobloxAuth:
    """
    Roblox authentication service.

    Handles:
    - Cookie validation
    - CSRF token retrieval
    - Authentication ticket generation (for game launching)
    """

    def __init__(self, http: RobloxHTTP):
        """
        Initialize auth service.

        Args:
            http: RobloxHTTP client instance
        """
        self._http = http

    async def get_csrf_token(self) -> Optional[str]:
        """
        Get a CSRF token from Roblox.

        The CSRF token is required for most authenticated POST requests.

        Returns:
            CSRF token string or None
        """
        return await self._http.fetch_csrf_token()

    async def get_authenticated_user(self) -> Optional[AuthenticatedUser]:
        """
        Get the currently authenticated user's information.

        Uses the cookie to fetch user details.

        Returns:
            AuthenticatedUser or None if not authenticated
        """
        resp = await self._http.get(
            "https://users.roblox.com/v1/users/authenticated"
        )

        if resp.status != 200 or not resp.data:
            return None

        return AuthenticatedUser(
            user_id=resp.data.get("id"),
            username=resp.data.get("name"),
            display_name=resp.data.get("displayName"),
        )

    async def validate_cookie(self) -> bool:
        """
        Validate that the current cookie is valid.

        Returns:
            True if cookie is valid, False otherwise
        """
        user = await self.get_authenticated_user()
        return user is not None

    async def get_authentication_ticket(self) -> Optional[str]:
        """
        Get an authentication ticket for game launching.

        This ticket is used in the roblox-player:// protocol URL
        to authenticate the game session.

        Returns:
            Authentication ticket string or None
        """
        # Ensure we have a CSRF token
        if not self._http._csrf_token:
            await self.get_csrf_token()

        resp = await self._http.post(
            "https://auth.roblox.com/v1/authentication-ticket",
            headers={
                "Referer": "https://www.roblox.com/",
                "Origin": "https://www.roblox.com",
            }
        )

        # The ticket comes in the response headers, not body
        ticket = resp.headers.get("rbx-authentication-ticket")
        if ticket:
            return ticket

        # Sometimes it's lowercase
        ticket = resp.headers.get("Rbx-Authentication-Ticket")
        return ticket

    async def get_user_id(self) -> Optional[int]:
        """Get the current user's ID."""
        user = await self.get_authenticated_user()
        return user.user_id if user else None
