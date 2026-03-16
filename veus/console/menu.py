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
        self.rq: Optional[Requester] = None
        self.user: Optional[User] = None
        self.guilds: Optional[Guilds] = None
        self.current_guild: Optional[Guild] = None
        self.last_channel_id: Optional[str] = None
        self.last_channel_name: Optional[str] = None
        self.last_messages: dict[str, list[dict]] = {} # suffix -> [{"id": full_id, "author": author, "content": content}]
        self.last_oldest_id: Optional[str] = None
        self.last_newest_id: Optional[str] = None
        self._running = True

    async def start(self):
        """Main entry point for the menu loop."""
        os.system("cls" if os.name == "nt" else "clear")
        
        # Minimalist & beautiful banner
        print(f"\n {Colors.FG_CYAN}veus{Colors.RESET} {Colors.FG_WHITE}· a shell discord experience{Colors.RESET}")
        print(f" {Colors.FG_WHITE}───────────────────────────{Colors.RESET}\n")
        
        await self.login()
        await self.main_loop()

    async def login(self):
        """Handle professional session setup via the Landing Zone."""
        if self.rq:
            await self.rq.shutdown()
            
        # Unified Setup (The Landing Zone)
        token, is_bot, verify, proxies = await self.tkh.setup_session(self.config)
        
        # Apply Proxies
        if proxies:
            self.proxy_mgr.add_proxies(proxies)
        
        # Initialize Requester
        self.rq = Requester(
            token, 
            is_bot, 
            self.logger, 
            proxy_mgr=self.proxy_mgr, 
            verify=verify
        )
        self.user = User(self.rq, self.logger)
        self.guilds = Guilds(self.rq, self.logger)

        # Senior Speedup: Parallelize initialization
        with self.logger.yaspin(text="Synchronizing profile and server list...", color="cyan"):
            await asyncio.gather(
                self.user.initialize(),
                self.guilds.fetch_all()
            )
            
        self.logger.success("Session initiated successfully.")

    async def main_loop(self):
        """Senior command loop with rich feedback."""
        # Setup persistent history
        history_path = os.path.expanduser("~/.veus_history")
        session = PromptSession(history=FileHistory(history_path))
        
        while self._running:
            prompt = self._get_prompt()
            try:
                # Dynamic completer setup
                completer = await cmd.get_completer(self)
                
                result = await session.prompt_async(
                    ANSI(prompt),
                    completer=completer,
                )
                
                if not result: continue
                
                parts = shlex.split(result)
                cmd_name = parts[0].lower()
                args = parts[1:]
                
                metadata = cmd.get_command(cmd_name)
                if metadata:
                    await self._execute_command(metadata, args)
                else:
                    self.logger.error(f"Command '{cmd_name}' not found. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("") # New line
                continue
            except Exception as e:
                self.logger.error(f"Critical error in loop: {e}")

    def _get_prompt(self) -> str:
        """Softer, chill prompt aesthetic."""
        user_part = f"{Colors.FG_MAGENTA}◖ {self.user.username} ◗{Colors.RESET}" if self.user else ""
        guild_part = f" {Colors.FG_CYAN}{self.current_guild.name}{Colors.RESET}" if self.current_guild else ""
        chan_part = f" {Colors.FG_WHITE}#{self.last_channel_name}{Colors.RESET}" if self.last_channel_name else ""
        
        return f"{user_part}{guild_part}{chan_part} {Colors.FG_WHITE}»{Colors.RESET} "

    async def _execute_command(self, metadata: Any, args: list[str]):
        """Sanitized command execution with interactive fallbacks."""
        try:
            # Check required arguments
            req_params = [p for p in metadata.params if p.default == inspect.Parameter.empty]
            
            # If arguments are missing, we'll try to prompt for them interactively
            # This is the "Senior" way - don't fail, assist.
            final_args = list(args)
            if len(final_args) < len(req_params):
                missing_count = len(req_params) - len(final_args)
                self.logger.info(f"Command '{metadata.name}' requires more info. Prompting...")
                
                # We handle specific commands with custom interactive logic
                if metadata.name == "message":
                    if len(final_args) == 0: # Missing channel and message
                        if not self.current_guild:
                            self.logger.error("No guild selected. Please select a guild first with 'guilds'.")
                            return
                            
                        channels = await self.current_guild.get_channels()
                        if not channels:
                            self.logger.error("No channels available in this guild.")
                            return
                        choices = [Choice(c['id'], c['name']) for c in channels if c['type'] == 0]
                        channel_id = await inquirer.fuzzy(message="Select Channel:", choices=choices).execute_async()
                        if not channel_id: return
                        final_args.append(channel_id)
                        
                        # Sync name for prompt
                        self.last_channel_id = channel_id
                        for c in choices:
                            if c.value == channel_id:
                                self.last_channel_name = c.name
                                break
                    
                    if len(final_args) == 1: # Missing message content
                        msg_content = await inquirer.text(message="Message:").execute_async()
                        final_args.append(msg_content)
                
                # For any other missing args, we do generic text prompts if no custom logic exists
                while len(final_args) < len(req_params):
                    p = req_params[len(final_args)]
                    val = await inquirer.text(message=f"Enter {p.name}:").execute_async()
                    final_args.append(val)

            if metadata.is_async:
                await metadata.func(self, *final_args)
            else:
                metadata.func(self, *final_args)
        except Exception as e:
            self.logger.error(f"Failed to execute '{metadata.name}': {e}")
