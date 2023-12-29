from .colors import Colors
from inspect import getframeinfo, stack
import sys, os


# \033[A\n
class Logger:

	def __init__(self, debug: bool = False) -> None:
		self._debug = debug
		self.username = ""

	def set_username(self, username: str):
		self.username = username

	def _get_file_info(self):
		_, _, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		return exc_tb.tb_lineno, fname

	def debug(self, message: str) -> None:
		if self._debug:
			caller = getframeinfo(stack()[1][0])
			print(
			    f"[{Colors.FG_BLUE}DEBUG{Colors.RESET}]{' [' if self.username else ''}{Colors.FG_BLUE}{self.username}{Colors.RESET}{']' if self.username else ''} {os.path.basename(caller.filename)}:{caller.lineno} {Colors.FG_WHITE}▶{Colors.RESET} {message}"
			)

	def info(self, message: str) -> None:
		print(
		    f"[{Colors.FG_BLUE}INF{Colors.RESET}]{' [' if self.username else ''}{Colors.FG_BLUE}{self.username}{Colors.RESET}{']' if self.username else ''} ▶ {message}"
		)

	def warn(self, message: str) -> None:
		caller = getframeinfo(stack()[1][0])
		print(
		    f"[{Colors.FG_YELLOW}WARN{Colors.RESET}]{' [' if self.username else ''}{Colors.FG_YELLOW}{self.username}{Colors.RESET}{']' if self.username else ''} {Colors.FG_YELLOW}▶ {message}{Colors.RESET}"
		)

	def success(self, message: str) -> None:
		print(
		    f"[{Colors.FG_LIGHT_GREEN}SUCCESS{Colors.RESET}]{' [' if self.username else ''}{Colors.FG_LIGHT_GREEN}{self.username}{Colors.RESET}{']' if self.username else ''} {Colors.FG_LIGHT_GREEN}▶ {message}{Colors.RESET}"
		)

	def fail(self, message: str) -> None:
		print(
		    f"[{Colors.FG_RED}FAIL{Colors.RESET}]{' [' if self.username else ''}{Colors.FG_RED}{self.username}{Colors.RESET}{']' if self.username else ''} {Colors.FG_RED}▶ {message}{Colors.RESET}"
		)

	def error(self, message: str, exc=False) -> None:
		if exc:
			err_line, fname = self._get_file_info()
			print(
			    f"[{Colors.FG_RED}ERR{Colors.RESET}] {Colors.FG_RED}{fname}:{err_line}{Colors.RESET} {Colors.FG_RED}▶ {message}{Colors.RESET}"
			)
		else:
			print(
			    f"[{Colors.FG_RED}ERR{Colors.RESET}] {Colors.FG_RED}▶ {message}{Colors.RESET}"
			)

	def critical(self, message: str, exc=False) -> None:
		if exc:
			crit_line, fname = self._get_file_info()
			print(
			    f"[{Colors.BG_RED}CRITICAL{Colors.RESET}] {Colors.BG_RED}{fname}:{crit_line}{Colors.RESET} {Colors.FG_RED}▶{Colors.RESET}  {Colors.BG_RED}{message}{Colors.RESET}"
			)
		else:
			print(
			    f"[{Colors.FG_RED}CRITICAL{Colors.RESET}] {Colors.FG_RED}▶{Colors.RESET} {Colors.BG_RED}{message}{Colors.RESET}"
			)
