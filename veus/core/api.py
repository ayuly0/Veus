import asyncio
import json
import httpx
from typing import Union, Any, Optional
from veus.console.logger import Logger

# Discord API Constants
DEFAULT_API_VERSION = 10
BASE_URL = "https://discord.com/api/v"

class API:
    """Unified API handler for Discord interactions using httpx."""
    
    def __init__(
        self, 
        token: str, 
        is_bot: bool, 
        logger: Logger, 
        api_version: int = DEFAULT_API_VERSION,
        proxy_mgr: Optional[Any] = None,
        verify: bool = True,
        show_logs: bool = True
    ) -> None:
        self.logger = logger
        self._api_version = api_version
        self._token = token
        self._is_bot = is_bot
        self._proxy_mgr = proxy_mgr
        self._verify = verify
        self._show_logs = show_logs
        self._rotation_lock = asyncio.Lock()
        
        self._headers = {
            "Authorization": f"{'Bot ' if is_bot else ''}{self._token}",
            "Content-Type": "application/json"
        }
        self._base_url = f"{BASE_URL}{self._api_version}"
        self.client = self._create_client()

    def _create_client(self, proxy: Optional[str] = None) -> httpx.AsyncClient:
        """Create a new httpx client, optionally with an async proxy transport."""
        mounts = None
        if proxy:
            # MUST use AsyncHTTPTransport for async clients
            mounts = {"all://": httpx.AsyncHTTPTransport(proxy=proxy, verify=self._verify)}
            
        return httpx.AsyncClient(
            headers=self._headers,
            timeout=360.0,
            mounts=mounts,
            verify=self._verify
        )

    async def rotate_proxy(self):
        """Switch the underlying client to use the next proxy (thread-safe)."""
        if not self._proxy_mgr: return
        
        async with self._rotation_lock:
            proxy = self._proxy_mgr.get_next()
            if proxy:
                # Close old client before replacing
                old_client = self.client
                self.client = self._create_client(proxy=proxy)
                await old_client.aclose()
                self.logger.info(f"Rotated to proxy: {Colors.FG_CYAN}{proxy}{Colors.RESET}")

    async def close(self):
        """Close the underlying httpx client."""
        await self.client.aclose()

    def _route(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    async def request(self, method: str, path: str, payload: dict = None, params: dict = None, silent: bool = False) -> tuple[dict, int]:
        """Base request method with rate-limiting, proxy rotation, and logging."""
        url = f"{self._base_url}/{path}"
        
        while True:
            try:
                # Track the active proxy for logging
                proxy_str = self._proxy_mgr.get_current() if self._proxy_mgr else "Direct"
                if not silent and self._show_logs:
                    self.logger.info(f"[{proxy_str}] {method} {path}")
                
                response = await self.client.request(
                    method, 
                    url, 
                    json=payload, 
                    params=params
                )
                
                if response.status_code == 429:
                    retry_after = response.json().get("retry_after", 1)
                    self.logger.warn(f"[{proxy_str}] Rate limited! Retrying after {retry_after}s.")
                    if self._proxy_mgr: await self.rotate_proxy() # Rotate on rate limit
                    await asyncio.sleep(retry_after)
                    continue
                    
                # Handle empty responses
                if response.status_code == 204:
                    return None, response.status_code
                    
                return response.json(), response.status_code
                
            except httpx.HTTPError as ex:
                self.logger.error(f"HTTP Request failed: {ex}", fatal=False)
                if self._proxy_mgr: await self.rotate_proxy() # Rotate on networking error
                return {}, 0
            except Exception as ex:
                self.logger.error(f"Unexpected error: {ex}", fatal=True)
                return {}, 0

    # Shorthand methods
    async def get(self, path: str, params: dict = None, silent: bool = False) -> tuple[dict, int]:
        return await self.request("GET", path, params=params, silent=silent)

    async def post(self, path: str, payload: dict = None, silent: bool = False) -> tuple[dict, int]:
        return await self.request("POST", path, payload=payload, silent=silent)

    async def patch(self, path: str, payload: Optional[dict] = None) -> tuple[Any, int]:
        return await self.request("PATCH", path, payload=payload)

    async def put(self, path: str, payload: Optional[dict] = None) -> tuple[Any, int]:
        return await self.request("PUT", path, payload=payload)

    async def delete(self, path: str, silent: bool = False) -> tuple[dict, int]:
        return await self.request("DELETE", path, silent=silent)
