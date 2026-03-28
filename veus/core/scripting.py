import os
import asyncio
from lupa import LuaRuntime
from veus.console.logger import Logger

class ScriptingEngine:
    """Lua-based scripting engine for event hooks and automation."""
    
    def __init__(self, ctx, logger: Logger, scripts_dir: str = "scripts"):
        self.ctx = ctx
        self.logger = logger
        self.scripts_dir = scripts_dir
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        
        # Hardened Sandbox: Remove dangerous Lua standard libraries to prevent RCE
        self.lua.execute('os = nil; io = nil; package = nil; debug = nil;')
        
        self._hooks = {}
        
        # Ensure scripts directory exists
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        # Expose context to Lua
        self._setup_globals()

    def _setup_globals(self):
        """Expose safe Python objects to the Lua environment."""
        g = self.lua.globals()
        
        # Wrapped logger for Lua
        def lua_info(msg): self.logger.info(f"[Lua] {msg}")
        def lua_success(msg): self.logger.success(f"[Lua] {msg}")
        def lua_error(msg): self.logger.error(f"[Lua] {msg}")
        
        g.print = lua_info
        g.info = lua_info
        g.success = lua_success
        g.error = lua_error
        
        # Registration helper for Lua
        def register_hook(event, callback):
            if event not in self._hooks:
                self._hooks[event] = []
            self._hooks[event].append(callback)
            self.logger.info(f"Registered Lua hook for event: {event}")
            
        g.register_hook = register_hook
        
        # Expose ctx partially (safe methods)
        def send_message(channel_id, content):
            asyncio.create_task(self.ctx.rq.api.post(f"channels/{channel_id}/messages", {"content": content}, silent=True))
            
        g.send_message = send_message

    def load_scripts(self):
        """Load all .lua files from the scripts directory."""
        if not os.path.exists(self.scripts_dir): return
        
        files = [f for f in os.listdir(self.scripts_dir) if f.endswith(".lua")]
        for f in files:
            path = os.path.join(self.scripts_dir, f)
            try:
                with open(path, "r") as file:
                    code = file.read()
                    self.lua.execute(code)
                self.logger.success(f"Executed Lua script: {f}")
            except Exception as e:
                self.logger.error(f"Failed to execute Lua script {f}: {e}")

    async def trigger(self, event, data):
        """Trigger registered Lua hooks for an event."""
        if event in self._hooks:
            for callback in self._hooks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"Error in Lua hook ({event}): {e}")
