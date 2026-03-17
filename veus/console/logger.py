import sys
import os
from datetime import datetime
from inspect import getframeinfo, stack
from typing import Any, Union, Optional
from contextlib import contextmanager
from yaspin import yaspin
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

    def _format_prefix(self, level: str, color: str) -> str:
        timestamp = f"{Colors.FG_WHITE}{self._get_timestamp()}{Colors.RESET}"
        level_tag = f"[{color}{level}{Colors.RESET}]"
        user_tag = f" [{color}{self.username}{Colors.RESET}]" if self.username else ""
        return f"{timestamp} {level_tag}{user_tag} ▶"

    def debug(self, message: Any) -> None:
        if self._debug:
            caller = getframeinfo(stack()[1][0])
            loc = f"{os.path.basename(caller.filename)}:{caller.lineno}"
            prefix = self._format_prefix("DEBUG", Colors.FG_BLUE)
            print(f"{prefix} {Colors.FG_BLUE}{loc}{Colors.RESET} {message}")

    def info(self, message: Any) -> None:
        prefix = self._format_prefix("INF", Colors.FG_CYAN)
        print(f"{prefix} {message}")

    def warn(self, message: Any) -> None:
        prefix = self._format_prefix("WARN", Colors.FG_YELLOW)
        print(f"{prefix} {Colors.FG_YELLOW}{message}{Colors.RESET}")

    def success(self, message: Any) -> None:
        prefix = self._format_prefix("PASS", Colors.FG_LIGHT_GREEN)
        print(f"{prefix} {Colors.FG_LIGHT_GREEN}{message}{Colors.RESET}")

    def error(self, message: Any, fatal: bool = False) -> None:
        level = "FATAL" if fatal else "ERR"
        prefix = self._format_prefix(level, Colors.FG_RED)
        print(f"{prefix} {Colors.FG_RED}{message}{Colors.RESET}")

    @contextmanager
    def yaspin(self, text: str, color: str = "yellow"):
        """Context manager for the yaspin spinner."""
        with yaspin(text=text, color=color) as sp:
            yield sp
