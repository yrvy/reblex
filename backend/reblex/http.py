"""
HTTP client for Roblox API requests.

Handles cookies, CSRF tokens, and proper headers.
"""

import aiohttp
import asyncio
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class Response:
    """HTTP response wrapper."""
    status: int
    data: Any
    headers: dict
    text: str


class RobloxHTTP:
    """
    HTTP client for Roblox API.

    Handles:
    - Cookie-based authentication
    - CSRF token management
    - Automatic retries on 403 with new CSRF token
    """

    BASE_HEADERS = {
        "User-Agent": "Roblox/WinInet",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://www.roblox.com",
        "Referer": "https://www.roblox.com/",
    }

    def __init__(self, cookie: Optional[str] = None):
        """
        Initialize the HTTP client.

        Args:
            cookie: The .ROBLOSECURITY cookie value
        """
        self._cookie = cookie
        self._csrf_token: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def cookie(self) -> Optional[str]:
        return self._cookie

    @cookie.setter
    def cookie(self, value: str):
        self._cookie = value

    def _get_cookie_header(self) -> str:
        """Build the cookie header string."""
        if not self._cookie:
            return ""
        # Handle both raw cookie value and full cookie string
        if self._cookie.startswith(".ROBLOSECURITY="):
            return self._cookie
        return f".ROBLOSECURITY={self._cookie}"

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def request(
        self,
        method: str,
        url: str,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        include_csrf: bool = True,
        retry_csrf: bool = True,
    ) -> Response:
        """
        Make an HTTP request to the Roblox API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            data: JSON body data
            headers: Additional headers
            include_csrf: Whether to include CSRF token
            retry_csrf: Whether to retry on 403 with new CSRF token

        Returns:
            Response object with status, data, headers
        """
        await self._ensure_session()

        req_headers = dict(self.BASE_HEADERS)

        if self._cookie:
            req_headers["Cookie"] = self._get_cookie_header()

        if include_csrf and self._csrf_token:
            req_headers["X-CSRF-TOKEN"] = self._csrf_token

        if headers:
            req_headers.update(headers)

        async with self._session.request(
            method,
            url,
            json=data,
            headers=req_headers,
        ) as resp:
            # Try to get JSON, fallback to text
            text = await resp.text()
            try:
                json_data = await resp.json() if text else None
            except:
                json_data = None

            response = Response(
                status=resp.status,
                data=json_data,
                headers=dict(resp.headers),
                text=text,
            )

            # Handle CSRF token from response
            if "x-csrf-token" in resp.headers:
                self._csrf_token = resp.headers["x-csrf-token"]

            # Retry on 403 if we got a new CSRF token
            if resp.status == 403 and retry_csrf and self._csrf_token:
                return await self.request(
                    method, url, data, headers,
                    include_csrf=True,
                    retry_csrf=False,  # Don't retry again
                )

            return response

    async def get(self, url: str, **kwargs) -> Response:
        """Make a GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, data: Optional[dict] = None, **kwargs) -> Response:
        """Make a POST request."""
        return await self.request("POST", url, data=data, **kwargs)

    async def fetch_csrf_token(self) -> Optional[str]:
        """
        Fetch a CSRF token from Roblox.

        Makes a POST to auth endpoint that returns 403 with CSRF token in headers.

        Returns:
            The CSRF token or None
        """
        await self._ensure_session()

        headers = dict(self.BASE_HEADERS)
        if self._cookie:
            headers["Cookie"] = self._get_cookie_header()

        try:
            async with self._session.post(
                "https://auth.roblox.com/v2/login",
                headers=headers,
            ) as resp:
                if "x-csrf-token" in resp.headers:
                    self._csrf_token = resp.headers["x-csrf-token"]
                    return self._csrf_token
        except:
            pass

        return None
