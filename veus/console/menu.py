import shlex
import inspect
import os
import asyncio
from typing import Optional, Any
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import ANSI

from veus.console.logger import Logger
from veus.console.token_handler import TokenHandler
from veus.console.registry import cmd
from veus.console.colors import Colors
from veus.console.commands import load_commands
from veus.core.requester import Requester
from veus.core.user import User
from veus.core.guild import Guild, Guilds

# Load modular commands
load_commands()

class Menu:
    """Modular CLI Menu and command dispatcher."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.tkh = TokenHandler(logger)
        from veus.core.config import ConfigManager
        self.config = ConfigManager()
        from veus.core.proxy_manager import ProxyManager
        self.proxy_mgr = ProxyManager(self.logger)
        self.proxy_mgr.strategy = self.config.get("proxy_strategy", "round-robin")
        
        # Session State
        self.rq: Optional[Requester] = None
        self.user: Optional[User] = None
        self.guilds: Optional[Guilds] = None
        self.current_guild: Optional[Guild] = None
        
        # Messaging Context (Soft State)
        self.last_channel_id: Optional[str] = None
        self.last_channel_name: Optional[str] = None
        self.last_messages: dict[str, list[dict]] = {} 
        self.last_oldest_id: Optional[str] = None
        self.last_newest_id: Optional[str] = None
        
        self._running = True

    async def start(self):
        """Main entry point for the menu loop."""
        os.system("clear" if os.name != "nt" else "cls")
        
        # Soft, chill, minimal banner
        print(f"\n {Colors.FG_MAGENTA}◌{Colors.RESET} {Colors.FG_WHITE}veus{Colors.RESET} {Colors.FG_CYAN}·{Colors.RESET} {Colors.FG_WHITE}shell{Colors.RESET}\n")
        
        await self.login()
        await self.main_loop()

    async def login(self):
        """Handle professional session setup via the Landing Zone."""
        if self.rq:
            await self.rq.shutdown()
            
        token, is_bot, verify, proxies = await self.tkh.setup_session(self.config)
        
        if proxies:
            self.proxy_mgr.add_proxies(proxies)
        
        self.rq = Requester(token, is_bot, self.logger, proxy_mgr=self.proxy_mgr, verify=verify)
        self.user = User(self.rq, self.logger)
        self.guilds = Guilds(self.rq, self.logger)

        with self.logger.yaspin(text="syncing setup...", color="magenta"):
            await asyncio.gather(
                self.user.initialize(),
                self.guilds.fetch_all()
            )
            
        self.logger.success("session live")

    async def main_loop(self):
        """Senior command loop with rich feedback."""
        history_path = os.path.expanduser(self.config.get("history_file", "~/.veus_history"))
        session = PromptSession(history=FileHistory(history_path))
        
        while self._running:
            prompt = self._get_prompt()
            try:
                completer = await cmd.get_completer(self)
                result = await session.prompt_async(ANSI(prompt), completer=completer)
                
                if not result: continue
                
                parts = shlex.split(result)
                cmd_name = parts[0].lower()
                args = parts[1:]
                
                metadata = cmd.get_command(cmd_name)
                if metadata:
                    await self._execute_command(metadata, args)
                else:
                    self.logger.error(f"command '{cmd_name}' unknown")
                    
            except KeyboardInterrupt:
                print("")
                continue
            except Exception as e:
                self.logger.error(f"loop error: {e}")

    def _get_prompt(self) -> str:
        """Minimalist, chill prompt aesthetic."""
        user = f"{Colors.FG_CYAN}◖{Colors.BG_SOFT_CYAN}{Colors.FG_WHITE} {self.user.username} {Colors.RESET}{Colors.FG_CYAN}◗{Colors.RESET}" if self.user else ""
        guild = f" {Colors.FG_MAGENTA}{self.current_guild.name}{Colors.RESET}" if self.current_guild else ""
        chan = f" {Colors.FG_WHITE}#{self.last_channel_name}{Colors.RESET}" if self.last_channel_name else ""
        
        return f"{user}{guild}{chan} {Colors.FG_CYAN}»{Colors.RESET} "

    async def _execute_command(self, metadata: Any, args: list[str]):
        """Decentralized command execution."""
        try:
            req_params = [p for p in metadata.params if p.default == inspect.Parameter.empty]
            
            final_args = list(args)
            if len(final_args) < len(req_params):
                self.logger.info(f"command '{metadata.name}' needs details...")
                while len(final_args) < len(req_params):
                    p = req_params[len(final_args)]
                    val = await inquirer.text(message=f"{p.name}:").execute_async()
                    if not val: return 
                    final_args.append(val)

            if metadata.is_async:
                await metadata.func(self, *final_args)
            else:
                metadata.func(self, *final_args)
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
