from typing import Union, Any, Optional
import asyncio
from veus.core.api import API
from veus.console.logger import Logger
import os
import httpx

class Requester:
    """Handles high-level request orchestration and mass-actions."""
    
    def __init__(self, token: str, is_bot: bool, logger: Logger, proxy_mgr: Optional[Any] = None, verify: bool = True, show_logs: bool = True):
        self.api = API(token, is_bot, logger, proxy_mgr=proxy_mgr, verify=verify, show_logs=show_logs)
        self.logger = logger
        self.vault: list[API] = [self.api] # Identity Vault
        
        # Store params for spawning new API instances
        self._is_bot = is_bot
        self._proxy_mgr = proxy_mgr
        self._verify = verify
        self._show_logs = show_logs

    def add_token(self, token: str, is_bot: bool = False):
        """Add a new identity to the vault."""
        new_api = API(token, is_bot, self.logger, proxy_mgr=self._proxy_mgr, verify=self._verify, show_logs=self._show_logs)
        self.vault.append(new_api)
        self.logger.success(f"Identity secured in vault. Total identities: {len(self.vault)}")

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

    async def download_file(self, url: str, dest_path: str) -> bool:
        """Download a file directly to disk with path traversal protection."""
        try:
            # Secure path resolution: restrict to downloads/ directory
            base_dir = os.path.abspath("downloads")
            safe_name = os.path.normpath("/" + dest_path).lstrip("/")
            full_path = os.path.abspath(os.path.join(base_dir, safe_name))
            
            if not full_path.startswith(base_dir):
                full_path = os.path.join(base_dir, os.path.basename(dest_path))
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200: return False
                    
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
            return True
        except Exception:
            return False

    async def mass_download(self, tasks: list[tuple[str, str]]) -> list[bool]:
        """Download multiple files concurrently."""
        semaphore = asyncio.Semaphore(5) # Conservative for binary downloads
        
        async def work(url, dest):
            async with semaphore:
                return await self.download_file(url, dest)
                
        actions = [work(url, dest) for url, dest in tasks]
        return await asyncio.gather(*actions)
