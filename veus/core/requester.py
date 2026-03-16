from typing import Union, Any, Optional
import asyncio
from veus.core.api import API
from veus.console.logger import Logger

class Requester:
    """Handles high-level request orchestration and mass-actions."""
    
    def __init__(self, token: str, is_bot: bool, logger: Logger, proxy_mgr: Optional[Any] = None, verify: bool = True):
        self.api = API(token, is_bot, logger, proxy_mgr=proxy_mgr, verify=verify)
        self.logger = logger

    async def shutdown(self):
        await self.api.close()

    async def mass_request(self, method: str, path: str, payloads: list[dict]) -> list[tuple[Any, int]]:
        """Executes multiple requests concurrently with a concurrency limit."""
        semaphore = asyncio.Semaphore(10) # Limit concurrency to avoid instant rate-limits
        
        async def task(payload):
            async with semaphore:
                return await self.api.request(method, path, payload=payload)
        
        tasks = [task(p) for p in payloads]
        return await asyncio.gather(*tasks)

    # High-level wrappers for common mass actions
    async def mass_post(self, path: str, payloads: list[dict]):
        return await self.mass_request("POST", path, payloads)

    async def mass_delete(self, paths: list[str]):
        """Special case for deleting multiple different paths."""
        semaphore = asyncio.Semaphore(10)
        
        async def task(path):
            async with semaphore:
                return await self.api.delete(path)
                
        tasks = [task(p) for p in paths]
        return await asyncio.gather(*tasks)
