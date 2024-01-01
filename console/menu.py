from InquirerPy.base.control import Choice
from .token_handler import TokenHandler
from .menu_handler import MenuHandler
from InquirerPy import inquirer
from .logger import Logger
from yaspin import yaspin

__import__("sys").path.append("../")
from core.requester import Requester
from core.user import User
import asyncio
import inspect
import shlex
from stem import Signal
from stem.control import Controller


def spin(func, text):
	def wrapper(*args, **kwargs):
		with yaspin(text=text, color="yellow") as _:
			func(*args, **kwargs)

	return wrapper


class Menu:
	def __init__(self):
		self.rq = None
		self.user = None
		self.token = None
		self.token_type = None
		self.current_guild = None
		self.current_guild_id = 0
		self.logger = Logger(debug=True)
		self.tkh = TokenHandler()
		self.menuHandler = MenuHandler(self.rq, self.logger)
		self.funcs = {
			"load_token": self.load_token,
			"clear": self.menuHandler.clear,
			"help": self.help,
			"exit": self.menuHandler.exit,
		}

	def control(self):
		while True:
			completer = {key: None for key in sorted(self.funcs)}
			completer["help"] = completer.copy()
			message = "▶"
			if self.user is not None:
				message = f"[{self.user.username}] ▶"
			if self.user is not None and self.current_guild is not None:
				message = f"[{self.user.username}] [{self.current_guild.name}] ▶"

			result = inquirer.text(
				message=message, completer=completer, qmark="", amark=""
			).execute()
			if result == "":
				continue

			res = shlex.split(result)
			try:
				if res[0] in self.funcs:
					# with Controller.from_port(port=9051) as controller:
					# 	controller.authenticate(password="somepass")
					# 	controller.signal(Signal.NEWNYM)
					self.logger.debug(
						self.funcs[res[0]](*res[1 : len(res) + 1])
						if len(res) > 1
						else self.funcs[res[0]]()
					)
				else:
					self.logger.error(f"Command '{res[0]}' doesnt exist.")
			except KeyboardInterrupt:
				continue
			except asyncio.CancelledError:
				continue
			except Exception as ex:
				self.logger.error(str(ex), True)

	def load_token(self):
		self.current_guild = None
		self.funcs = {
			"load_token": self.load_token,
			"clear": self.menuHandler.clear,
			"help": self.help,
			"exit": self.menuHandler.exit,
		}

		self.token, self.is_bot = self.tkh.get_token()
		with yaspin(text="Initiating...", color="yellow") as _:
			self.rq = Requester(9, self.token, logger=self.logger, is_bot=self.is_bot)
			self.user = User(self.rq)

		self.menuHandler.user = self.user
		funcs = [
			self.select_guild,
			self.user.send_dm_by_id,
			self.user.update_profile,
			self.user.update_global_name,
			self.user.update_settings,
			self.user.get_dms,
			self.menuHandler.send_dms,
		]

		for func in funcs:
			self.add_func(func)

	def select_guild(self):
		choices = [
			Choice(value=guild_id, name=self.user.guilds.guild_ids[guild_id])
			for guild_id in self.user.guilds.guild_ids
		]
		self.current_guild_id = inquirer.fuzzy(
			message="Select Guild:", choices=choices, qmark="▶", amark="▶"
		).execute()
		self.user.guilds.load_guild(
			self.current_guild_id
		) if self.current_guild_id not in self.user.guilds.loaded_guilds else None
		self.current_guild: Guild = self.user.guilds.loaded_guilds[
			self.current_guild_id
		]
		self.menuHandler.current_guild = self.current_guild
		funcs = [
			self.current_guild.send_message_by_channel_id,
			self.current_guild.send_webhook_message,
			self.current_guild.create_channels,
			self.current_guild.delete_all_channels,
			self.current_guild.delete_all_roles,
			self.current_guild.change_guild_name,
			self.current_guild.change_guild_icon,
			self.current_guild.create_webhook,
			self.current_guild.create_roles,
			self.current_guild.delete_channel_by_id,
			self.current_guild.delete_emoji_by_id,
			self.current_guild.delete_all_emojis,
			self.current_guild.delete_role_by_id,
			self.current_guild.kick_user_by_id,
			self.current_guild.kick_all_users,
			self.current_guild.ban_user_by_id,
			self.current_guild.ban_all_users,
			self.current_guild.leave_guild,
			self.current_guild.delete_guild,
			self.current_guild.create_invite_link,
			self.menuHandler.delete_channels,
			self.menuHandler.send_messages_channels,
		]
		for func in funcs:
			self.add_func(func)

	def add_func(self, func):
		self.funcs[func.__name__] = func

	def help(self, command: str = "", *_):
		if command not in self.funcs and command is not None:
			self.logger.error(f"Command '{command}' doesnt exist.")
			return

		if command is not None:
			parameters = inspect.signature(self.funcs[command]).parameters
			help_command = f"Use: {command}"
			for parameter in parameters:
				help_command += f" {parameters[parameter]},"
			print(help_command)
			return

		cmds = [cmd for cmd in sorted(self.funcs)]
		help_menu = "\n• Command Available:\n"
		for cmd in cmds:
			help_menu += f"    • {cmd}\n"
		help_menu += "Use: help <command> for more info.\n"
		print(help_menu)
