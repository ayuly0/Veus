import shlex
import inspect
import os
import asyncio
from typing import Optional, Any
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from prompt_toolkit.shortcuts import PromptSession, print_formatted_text
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.patch_stdout import patch_stdout

from veus.console.logger import Logger
from veus.console.token_handler import TokenHandler
from veus.console.registry import cmd
from veus.console.colors import Colors
from veus.console.commands import load_commands
from veus.core.requester import Requester
from veus.core.user import User
from veus.core.guild import Guild, Guilds
from veus.core.gateway import Gateway
from veus.core.scripting import ScriptingEngine

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
        self.gateway: Optional[Gateway] = None
        
        # Messaging Context (Soft State)
        self.last_channel_id: Optional[str] = None
        self.last_channel_name: Optional[str] = None
        self.last_messages: dict[str, list[dict]] = {} 
        self.last_oldest_id: Optional[str] = None
        self.last_newest_id: Optional[str] = None
        
        # Scripting Engine
        self.scripting = ScriptingEngine(self, self.logger)
        
        self._running = True

    async def start(self):
        """Main entry point for the menu loop."""
        os.system("clear" if os.name != "nt" else "cls")
        
        # Soft, initial entry banner
        print_formatted_text(ANSI(f"\n {Colors.FG_MAGENTA}◌{Colors.RESET} {Colors.FG_WHITE}veus{Colors.RESET} {Colors.FG_CYAN}·{Colors.RESET} {Colors.FG_WHITE}shell established{Colors.RESET}\n"))
        
        await self.login()
        await self.main_loop()

    async def login(self):
        """Handle professional session setup via the Landing Zone."""
        if self.rq:
            await self.rq.shutdown()
            
        token, is_bot, verify, proxies = await self.tkh.setup_session(self.config)
        
        if proxies:
            self.proxy_mgr.add_proxies(proxies)
        
        show_logs = self.config.get("show_proxy_logs", True)
        self.rq = Requester(token, is_bot, self.logger, proxy_mgr=self.proxy_mgr, verify=verify, show_logs=show_logs)
        self.user = User(self.rq, self.logger)
        self.guilds = Guilds(self.rq, self.logger)

        with self.logger.yaspin(text="syncing setup...", color="magenta"):
            await asyncio.gather(
                self.user.initialize(),
                self.guilds.fetch_all()
            )
            
        # Initialize and Start Gateway for real-time features
        self.gateway = Gateway(token, is_bot, self.logger)
        asyncio.create_task(self.gateway.connect())
        
        # Register "The Eye" listener
        self.gateway.on("MESSAGE_CREATE", self._handle_live_message)
        
        # Register Scripting Engine hooks
        self.gateway.on("MESSAGE_CREATE", lambda d: asyncio.create_task(self.scripting.trigger("MESSAGE_CREATE", d)))
        self.scripting.load_scripts()
            
        # Display the Senior Dashboard
        self._display_dashboard()

    def _display_dashboard(self):
        """High-impact dashboard showing identity and state."""
        os.system("clear" if os.name != "nt" else "cls")
        
        print_formatted_text(ANSI(f"\n {Colors.FG_MAGENTA}◌{Colors.RESET} {Colors.FG_WHITE}veus{Colors.RESET} {Colors.FG_CYAN}·{Colors.RESET} {Colors.FG_WHITE}dashboard{Colors.RESET}"))
        print_formatted_text(ANSI(f" {Colors.FG_WHITE}──────────────────────────────────────────{Colors.RESET}"))
        
        # Identity Section
        name = self.user.global_name or self.user.username
        print_formatted_text(ANSI(f" {Colors.FG_CYAN}IDENTITY  {Colors.RESET} {Colors.FG_WHITE}{name} ({self.user.username}){Colors.RESET}"))
        print_formatted_text(ANSI(f" {Colors.FG_CYAN}ID        {Colors.RESET} {Colors.FG_WHITE}{self.user.user_id}{Colors.RESET}"))
        
        # Stats Section
        guild_count = len(self.guilds.items) if self.guilds else 0
        print_formatted_text(ANSI(f" {Colors.FG_CYAN}SERVERS   {Colors.RESET} {Colors.FG_WHITE}{guild_count} active contexts{Colors.RESET}"))
        
        # Connection/Settings Section
        ssl = "ENABLED" if self.config.get("ssl_verify", True) else "DISABLED"
        api_v = self.config.get("api_version", 9)
        print_formatted_text(ANSI(f" {Colors.FG_CYAN}NETWORK   {Colors.RESET} {Colors.FG_WHITE}API v{api_v} | SSL: {ssl}{Colors.RESET}"))
        
        proxy = self.proxy_mgr.get_current() or "Direct"
        print_formatted_text(ANSI(f" {Colors.FG_CYAN}VIA       {Colors.RESET} {Colors.FG_WHITE}{proxy}{Colors.RESET}"))
        
        print_formatted_text(ANSI(f" {Colors.FG_WHITE}──────────────────────────────────────────{Colors.RESET}\n"))
        self.logger.success("session live and secured")

    async def main_loop(self):
        """Senior command loop with rich feedback."""
        history_path = os.path.expanduser(self.config.get("history_file", "~/.veus_history"))
        session = PromptSession(history=FileHistory(history_path))
        
        with patch_stdout():
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
        """Standardized shell identity prompt, hybrid layout."""
        padding = " "
        user = Colors.tag(self.user.username, bg=Colors.BG_SOFT_CYAN, fg=Colors.FG_WHITE) if self.user else ""
        guild = f" {Colors.FG_MAGENTA}{self.current_guild.name}{Colors.RESET}" if self.current_guild else ""
        chan = f" {Colors.FG_WHITE}#{self.last_channel_name}{Colors.RESET}" if self.last_channel_name else ""
        
        return f"{padding}{user}{guild}{chan}{Colors.FG_CYAN} »{Colors.RESET} "

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

    async def _handle_live_message(self, data: dict):
        """Internal listener for 'The Eye' global monitor."""
        # Don't log our own messages
        if self.user and data.get("author", {}).get("id") == self.user.id:
            return
            
        author = data.get("author", {}).get("username", "Unknown")
        content = data.get("content", "")
        # Only log if it's a mention or DM (Identity Vault awareness)
        # Simplified for now: Log all messages in a "chill" way if the user enables it
        if self.config.get("eye_monitor", False):
            # Use a soft prefix for live messages
            self.logger.info(f"{Colors.FG_MAGENTA}◌{Colors.RESET} {Colors.FG_WHITE}{author}{Colors.RESET}: {content}", prefix="EYE")
