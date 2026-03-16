from typing import Optional, Any
from veus.core.requester import Requester
from veus.console.logger import Logger

class User:
    """Represents the current Discord user."""
    
    def __init__(self, requester: Requester, logger: Logger):
        self.rq = requester
        self.logger = logger
        self.user_id: Optional[str] = None
        self.username: str = ""
        self.global_name: Optional[str] = None
        
    async def initialize(self):
        """Fetch current user profile."""
        data, status = await self.rq.api.get("users/@me", silent=True)
        if status == 200:
            self.data = data
            self.id = data["id"]
            self.user_id = data["id"] # Keep user_id for consistency with other parts of the class
            self.username = data["username"]
            self.global_name = data.get("global_name")
            self.logger.set_username(self.username)
        else:
            self.logger.error("Failed to initialize user", fatal=True)

    async def get_dms(self) -> list:
        data, _ = await self.rq.api.get("users/@me/channels")
        return data if isinstance(data, list) else []

    async def update_profile(self, bio: Optional[str] = None) -> bool:
        payload = {}
        if bio: payload["bio"] = bio
        
        _, status = await self.rq.api.patch("users/@me", payload)
        return status == 200

    async def send_dm(self, recipient_id: str, content: str, amount: int = 1):
        # First, ensure we have a DM channel
        data, status = await self.rq.api.post("users/@me/channels", {"recipient_id": recipient_id})
        if status != 200:
            self.logger.error(f"Failed to open DM with {recipient_id}")
            return
            
        channel_id = data["id"]
        payloads = [{"content": content} for _ in range(amount)]
        await self.rq.mass_post(f"channels/{channel_id}/messages", payloads)
