import sys
import os
from datetime import datetime
from inspect import getframeinfo, stack
from typing import Any, Union, Optional
from contextlib import contextmanager
from yaspin import yaspin
from prompt_toolkit import print_formatted_text, ANSI
from veus.console.colors import Colors

class Logger:
    """Enhanced logger for premium terminal output."""
    
    def __init__(self, debug: bool = False) -> None:
        self._debug = debug
        self.username = ""

    def set_username(self, username: str):
        self.username = username

    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _format_prefix(self, level: str, level_bg: str, level_fg: str) -> str:
        timestamp = f"{Colors.FG_WHITE}{self._get_timestamp()}{Colors.RESET}"
        # Industrial style: Square brackets with background colors restored
        level_tag = f"{Colors.FG_CYAN}[{Colors.RESET}{level_bg}{level_fg} {level} {Colors.RESET}{Colors.FG_CYAN}]{Colors.RESET}"
        # Identity stays as a rounded pill to match the new prompt identity style
        user_tag = f" {Colors.tag(self.username, bg=Colors.BG_SOFT_CYAN, fg=Colors.FG_WHITE)}" if self.username else ""
        return f" {timestamp} {level_tag}{user_tag}{Colors.FG_CYAN} »{Colors.RESET}"

    def debug(self, message: Any) -> None:
        if self._debug:
            caller = getframeinfo(stack()[1][0])
            loc = f"{os.path.basename(caller.filename)}:{caller.lineno}"
            prefix = self._format_prefix("DEBUG", Colors.BG_BLUE, Colors.FG_WHITE)
            print_formatted_text(ANSI(f"{prefix}  {Colors.FG_BLUE}{loc}{Colors.RESET} {message}"))

    def info(self, message: Any, prefix: Optional[str] = None) -> None:
        level = prefix if prefix else "INF"
        prefix_str = self._format_prefix(level, Colors.BG_CYAN, Colors.FG_WHITE)
        print_formatted_text(ANSI(f"{prefix_str}  {message}"))

    def warn(self, message: Any, prefix: Optional[str] = None) -> None:
        level = prefix if prefix else "WARN"
        prefix_str = self._format_prefix(level, Colors.BG_YELLOW, Colors.FG_BLACK)
        print_formatted_text(ANSI(f"{prefix_str}  {Colors.FG_YELLOW}{message}{Colors.RESET}"))

    def success(self, message: Any, prefix: Optional[str] = None) -> None:
        level = prefix if prefix else "PASS"
        prefix_str = self._format_prefix(level, Colors.BG_GREEN, Colors.FG_WHITE)
        print_formatted_text(ANSI(f"{prefix_str}  {Colors.FG_LIGHT_GREEN}{message}{Colors.RESET}"))

    def error(self, message: Any, fatal: bool = False, prefix: Optional[str] = None) -> None:
        level = prefix if prefix else ("FATAL" if fatal else "ERR")
        prefix_str = self._format_prefix(level, Colors.BG_RED, Colors.FG_WHITE)
        print_formatted_text(ANSI(f"{prefix_str}  {Colors.FG_RED}{message}{Colors.RESET}"))

    @contextmanager
    def yaspin(self, text: str, color: str = "yellow"):
        """Context manager for the yaspin spinner."""
        with yaspin(text=text, color=color) as sp:
            yield sp
