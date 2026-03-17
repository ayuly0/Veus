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

    async def ban(self, user_id: str, reason: Optional[str] = None) -> bool:
        """Ban a member from the guild."""
        payload = {"delete_message_days": 1, "reason": reason} if reason else {"delete_message_days": 1}
        _, status = await self.rq.api.put(f"guilds/{self.id}/bans/{user_id}", payload)
        return status in [201, 204]

    async def kick(self, user_id: str, reason: Optional[str] = None) -> bool:
        """Kick a member from the guild."""
        # Discord usually expects reason in Audit Log headers or query params for kick
        url = f"guilds/{self.id}/members/{user_id}"
        if reason: url += f"?reason={reason}"
        _, status = await self.rq.api.delete(url)
        return status == 204

    async def create_channels(self, name: str, channel_type: int = 0, amount: int = 1):
        """Mass create channels."""
        payloads = [{"name": name, "type": channel_type} for _ in range(amount)]
        await self.rq.mass_post(f"guilds/{self.id}/channels", payloads)

    async def change_nickname(self, nickname: str) -> bool:
        """Change current user's nickname in this guild."""
        payload = {"nick": nickname}
        _, status = await self.rq.api.patch(f"guilds/{self.id}/members/@me", payload)
        return status == 200

    async def update_guild(self, **kwargs) -> bool:
        """Update guild settings (name, icon, banner, description, etc.)."""
        import base64
        import os
        
        payload = {}
        for key, value in kwargs.items():
            if value is None: continue
            
            # Handle images (icon, banner, splash)
            if key in ["icon", "banner", "splash"] and os.path.isfile(value):
                try:
                    with open(value, "rb") as f:
                        buf = f.read()
                        ext = os.path.splitext(value)[1].replace(".", "")
                        if ext == "jpg": ext = "jpeg"
                        b64 = base64.b64encode(buf).decode()
                        payload[key] = f"data:image/{ext};base64,{b64}"
                except Exception as e:
                    self.logger.error(f"Failed to process {key}: {e}")
            else:
                payload[key] = value
                
        if not payload: return False
        
        _, status = await self.rq.api.patch(f"guilds/{self.id}", payload)
        return status == 200

    async def get_webhooks(self) -> list[dict]:
        """Fetch all webhooks in the guild."""
        data, status = await self.rq.api.get(f"guilds/{self.id}/webhooks")
        return data if status == 200 else []

    async def create_webhook(self, channel_id: str, name: str) -> Optional[dict]:
        """Create a new webhook in a channel."""
        data, status = await self.rq.api.post(f"channels/{channel_id}/webhooks", {"name": name})
        return data if status == 200 else None

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        _, status = await self.rq.api.delete(f"webhooks/{webhook_id}")
        return status == 204

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
