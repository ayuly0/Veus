import asyncio
from typing import Optional, Any
from veus.core.requester import Requester
from veus.console.logger import Logger

class Guild:
    """Represents a Discord Guild (Server)."""
    
    def __init__(self, rq, logger: Logger, guild_id: str):
        self.rq = rq
        self.logger = logger
        self.id = guild_id
        self.name = "Unknown Guild"
        self._channels_cache: list[dict] = []

    async def initialize(self):
        """Fetch basic guild info."""
        data, status = await self.rq.api.get(f"guilds/{self.id}", silent=True)
        if status == 200:
            self.name = data.get("name", "Unknown")

    async def get_channels(self, force: bool = False) -> list[dict]:
        """Fetch channels for this specific guild (with caching)."""
        if self._channels_cache and not force:
            return self._channels_cache
            
        data, status = await self.rq.api.get(f"guilds/{self.id}/channels")
        if status == 200:
            self._channels_cache = data
            return data
        return []

    async def delete_channels(self, channel_ids: list[str]):
        """Mass delete channels by ID."""
        tasks = [self.rq.api.delete(f"channels/{cid}") for cid in channel_ids]
        await asyncio.gather(*tasks)

class Guilds:
    """Manages the user's guilds/servers."""
    
    def __init__(self, rq, logger: Logger):
        self.rq = rq
        self.logger = logger
        self.items: dict[str, str] = {} # ID -> Name

    async def fetch_all(self):
        data, status = await self.rq.api.get("users/@me/guilds", silent=True)
        if status == 200:
            self.items = {g["id"]: g["name"] for g in data}
        else:
            self.logger.error("Failed to fetch guilds")
