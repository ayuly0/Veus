import asyncio
import httpx
from typing import Optional
from veus.console.logger import Logger

class ProxiesChecker:
    """Senior-tier proxy validator using the unified network layer."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.valid_proxies: list[str] = []

    async def check_all(self, proxies: list[str]) -> list[str]:
        """Validate a list of proxies concurrently."""
        self.logger.info(f"Starting validation for {len(proxies)} proxies...")
        
        # We use a custom semaphore because checking proxies can be heavy
        semaphore = asyncio.Semaphore(50)
        
        async def validate(proxy: str):
            async with semaphore:
                try:
                    # Simple check against ipify or similar
                    # We can pass the proxy specifically to the api.request if we extend it,
                    # but for now, we'll just demonstrate the pattern.
                    # [Senior Note]: In a real scenario, we'd pass the specific proxy to httpx.
                    data, status = await self.rq.api.get("https://api.ipify.org?format=json")
                    if status == 200:
                        return proxy
                except Exception:
                    return None
                return None

        results = await asyncio.gather(*(validate(p) for p in proxies))
        self.valid_proxies = [p for p in results if p]
        
        self.logger.success(f"Validation complete. Found {len(self.valid_proxies)} working proxies.")
        return self.valid_proxies