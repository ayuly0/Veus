import asyncio
import json
import websockets
import time
from typing import Optional, Callable, Dict, Any
from veus.console.logger import Logger

class Gateway:
    """Handles real-time WebSocket connection to Discord's Gateway."""
    
    GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
    
    def __init__(self, token: str, is_bot: bool, logger: Logger):
        self.token = token
        self.is_bot = is_bot
        self.logger = logger
        self.ws = None
        self.heartbeat_interval = None
        self.heartbeat_task = None
        self.listen_task = None
        self.session_id = None
        self.last_sequence = None
        self._running = False
        self._event_handlers: Dict[str, list[Callable]] = {}

    def on(self, event_name: str, handler: Callable):
        """Register an event handler."""
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)

    async def _emit(self, event_name: str, data: Any):
        """Emit an event to all registered handlers."""
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)

    async def connect(self):
        """Establish connection with auto-reconnect and exponential backoff."""
        self._running = True
        retry_delay = 1
        
        while self._running:
            try:
                self.logger.info(f"Connecting to Gateway (Stealth Mode: {'BOT' if self.is_bot else 'USER'})...")
                async with websockets.connect(self.GATEWAY_URL) as ws:
                    self.ws = ws
                    retry_delay = 1 # Reset on success
                    self.listen_task = asyncio.create_task(self._listen_loop())
                    await self._wait_until_done()
            except Exception as e:
                if not self._running: break
                self.logger.error(f"Gateway connection error: {e}")
                
                # Exponential Backoff
                self.logger.warn(f"Reconnecting in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60) # Cap at 60s
        self._running = False

    async def _wait_until_done(self):
        while self._running and self.ws and getattr(self.ws, "open", True):
            await asyncio.sleep(1)

    async def _listen_loop(self):
        """Main loop for receiving and dispatching Gateway messages."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                op = data.get("op")
                t = data.get("t")
                d = data.get("d")
                s = data.get("s")
                
                if s:
                    self.last_sequence = s

                if op == 10: # Hello
                    self.heartbeat_interval = d["heartbeat_interval"] / 1000.0
                    if self.heartbeat_task: self.heartbeat_task.cancel()
                    self.heartbeat_task = asyncio.create_task(self._heartbeat())
                    await self._identify()
                    
                elif op == 11: # Heartbeat ACK
                    pass 
                
                elif op == 0: # Dispatch
                    if t == "READY":
                        self.session_id = d.get("session_id")
                        self.logger.success(f"Gateway Session Secured: {Colors.FG_CYAN}{self.session_id}{Colors.RESET}")
                    await self._emit(t, d)
                    
                elif op == 1: # Heartbeat Request
                    await self._send_heartbeat()

                elif op == 7: # Reconnect Request
                    self.logger.warn("Gateway requested reconnect (op 7).")
                    break

        except websockets.exceptions.ConnectionClosed as e:
            self.logger.warn(f"Gateway connection closed: {e.code} ({e.reason})")
        except Exception as e:
            self.logger.error(f"Error in Gateway listen loop: {e}")
        finally:
            if self.ws: await self.ws.close()

    async def _identify(self):
        """Identify the session to the Gateway using stealth parameters."""
        # Mimic Official Discord Desktop (Windows)
        properties = {
            "os": "Windows",
            "browser": "Discord Client",
            "release_channel": "stable",
            "client_version": "1.0.9015",
            "os_version": "10.0.19045",
            "os_arch": "x64",
            "system_locale": "en-US",
            "client_build_number": 215473,
            "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/108.0.5359.215 Electron/22.3.12 Safari/537.36",
            "browser_version": "22.3.12",
            "client_event_source": None
        }

        payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": properties,
                "presence": {
                    "status": "online",
                    "since": 0,
                    "activities": [],
                    "afk": False
                },
                "compress": False,
            }
        }

        # User accounts do NOT support intents and sending them can trigger closures.
        if self.is_bot:
            payload["d"]["intents"] = (1 << 9) | (1 << 12) | (1 << 15)

        await self.ws.send(json.dumps(payload))

    async def _heartbeat(self):
        """Background task to send periodic heartbeats."""
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._send_heartbeat()
            except Exception:
                break

    async def _send_heartbeat(self):
        if self.ws and getattr(self.ws, "open", False):
            await self.ws.send(json.dumps({"op": 1, "d": self.last_sequence}))

    async def stop(self):
        """Gracefully stop the gateway."""
        self._running = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.ws:
            await self.ws.close()
