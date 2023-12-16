__import__('sys').path.append('../')
from InquirerPy.validator import EmptyInputValidator
from InquirerPy.base.control import Choice
from .token_handler import TokenHandler
from core.requester import Requester
from core.guild import ChannelTypes
from InquirerPy import inquirer
from threading import Thread
from core.user import User
from .logger import Logger
from yaspin import yaspin
import asyncio
import inspect
import shlex
import os

class UserFeautes:
	UPDATE_BIO = 0
	UPDATE_GLOBAL_NAME = 1
	UPDATE_SETTINGS = 2
	SEND_DM_MESSAGE = 3
	CALL_DM = 4
	CLOSE_DM = 5
	UNFRIEND = 6
	BLOCK_USER = 7

def spin(func, text):
	def wrapper(*args, **kwargs):
		with yaspin(text=text, color="yellow") as sp:
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
		self.logger = Logger(debug = True)
		self.tkh = TokenHandler()
		self.funcs = {
			"load_token": self.load_token,
			"clear": self.clear_sc,
			"help": self.help,
			"exit": self.exit,
		}

	def control(self):
		while True:
			completer = {
				key: None for key in sorted(self.funcs)
			}
			completer["help"] = completer.copy()
			message = "▶"
			if self.user != None:
				message = f"[{self.user.username}] ▶"
			if self.user != None and self.current_guild != None:
				message = f"[{self.user.username}] [{self.current_guild.name}] ▶"

			result = inquirer.text(message = message, completer=completer, qmark="", amark="").execute()
			if result == "":
				continue

			res = shlex.split(result)
			try:
				if res[0] in self.funcs:
					self.logger.debug(self.funcs[res[0]](*res[1:len(res)+1]) if len(res) > 1 else self.funcs[res[0]]())
				else:
					self.logger.error(f"Command '{res[0]}' doesnt exist.")
			except KeyboardInterrupt:
				continue
			except asyncio.CancelledError:
				continue
			except Exception as ex:
				self.logger.error(ex, True)

	def load_token(self):
		# Refesh #
		self.current_guild = None
		self.funcs = {
			"load_token": self.load_token,
			"clear": self.clear_sc,
			"help": self.help,
			"exit": self.exit,
		}

		self.token, self.token_type = self.tkh.get_token()
		with yaspin(text="Initiating...", color="yellow") as sp:
			self.rq = Requester(9, self.token, logger = self.logger, token_type = self.token_type)
			self.user = User(self.rq)
		funcs = [
			self.select_guild,
			self.user.send_dm_message,
			self.user.update_profile,
			self.user.update_global_name,
			self.user.update_settings,
		]

		for func in funcs:
			self.add_func(func)

	def select_guild(self):
		choices = []
		for guild_id in self.user.guilds.guild_ids:
			choices.append(Choice(value = guild_id, name = self.user.guilds.guild_ids[guild_id]))
		self.current_guild_id = inquirer.fuzzy( message = "Select Guild:", choices = choices, qmark='▶', amark='▶').execute()
		if self.current_guild_id not in self.user.guilds.loaded_guilds:
			self.user.guilds.load_guild(self.current_guild_id)
		self.current_guild = self.user.guilds.loaded_guilds[self.current_guild_id]
		funcs = [
				self.current_guild.send_message,
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
				self.delete_channels,
				self.send_message_to_channels
				]
		for func in funcs:
			self.add_func(func)

	def add_func(self, func):
		self.funcs[func.__name__] = func

	def help(self, command: str = None, *args):
		if command not in self.funcs and command != None:
			self.logger.error(f"Command '{command}' doesnt exist.")
			return

		if command != None:
			parameters = inspect.signature(self.funcs[command]).parameters
			help_command = f"Use: {command}"
			for parameter in parameters:
				help_command += f" {parameters[parameter]},"
			print(help_command)
			return

		cmds = [cmd for cmd in sorted(self.funcs)]
		help_menu = f"""\n• Command Available:\n"""
		for cmd in cmds:
			help_menu += f"    • {cmd}\n"
		help_menu += "Use: help <command> for more info.\n"
		print(help_menu)

	def guild_control(self):
		pass

	def clear_sc(self):
		if os.name == "nt":
			os.system("cls")
		else:
			os.system("clear")

	## some funcs ##
	def delete_channels(self) -> None:
		all_channels, status = self.current_guild.get_all_channels()
		self.logger.debug(all_channels)
		channels = []
		channel_types = {ChnnaelTypes.GUILD_TEXT: "text", ChnnaelTypes.GUILD_VOICE: "voice", ChnnaelTypes.GUILD_CATEGORY: "cagetory"}
		for channel in all_channels:
			channels.append(Choice(value = channel["id"], name = f'{channel["name"]} ({channel_types[channel["type"]]})'))

		select_channels =  inquirer.checkbox(message = "Select Channels:", choices = channels, qmark='▶', amark='▶').execute()

		self.current_guild.delete_channels(select_channels)

	def send_message_to_channels(self):
		all_channels, status = self.current_guild.get_all_channels()
		channels = []
		for channel in all_channels:
			if channel["type"] != 0:
				continue
			channels.append(Choice(value = channel["id"], name = channel["name"]))
		select_channels = inquirer.checkbox(message = "Select Channels:", choices = channels, qmark='▶', amark='▶').execute()
		message = inquirer.text(message="Message:", qmark='▶', amark='▶').execute()
		tts = inquirer.confirm(message="TTS?", default=False, qmark='▶', amark='▶').execute()
		amount = inquirer.number(
		        message="Amount:",
				min_allowed=0,
				validate = EmptyInputValidator(), qmark='▶', amark='▶'
		).execute()

		if not select_channels:
			return

		threads = [Thread(target = self.current_guild.send_message, args = (channel_id, message, tts, amount,)) for channel_id in select_channels]
		for thread in threads:
			thread.start()
			
		for thread in threads:
			thread.join()

	def exit(self):
		__import__("os")._exit(1)