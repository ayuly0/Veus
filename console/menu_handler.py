__import__('sys').path.append('../')
from helpers.methods import thread_runner, split_list
from InquirerPy.validator import EmptyInputValidator
from InquirerPy.base.control import Choice
from core.guild import ChannelTypes
from InquirerPy import inquirer
from threading import Thread
import os

class MenuHandler:
	def __init__(self, rq, logger):
		self.rq = rq
		self.logger = logger
		self.current_guild = None
		self.user = None

	def delete_channels(self) -> None:
		all_channels, status = self.current_guild.get_all_channels()
		self.logger.debug(all_channels)
		channel_types = {ChannelTypes.GUILD_TEXT: "text", ChannelTypes.GUILD_VOICE: "voice", ChannelTypes.GUILD_CATEGORY: "cagetory"}
		channels = [Choice(value = channel["id"], name = f'{channel["name"]} ({channel_types[channel["type"]]})') for channel in all_channels]
		select_channels =  inquirer.checkbox(message = "Select Channels:", choices = channels, qmark='▶', amark='▶').execute()

		self.current_guild.delete_channels(select_channels)

	def send_messages_channels(self):
		all_channels, status = self.current_guild.get_all_channels()
		channels = []
		for channel in all_channels:
			if channel["type"] != 0:
				continue
			channels.append(Choice(value = channel["id"], name = channel["name"]))
		select_channels = inquirer.checkbox(message = "Select Channels:", choices = channels, qmark='▶', amark='▶').execute()
		message = inquirer.text(message="Message:", qmark='▶', amark='▶').execute()
		tts = inquirer.confirm(message="TTS?", default=False, qmark='▶', amark='▶').execute()
		amount = inquirer.number(message="Amount:", min_allowed=0, validate = EmptyInputValidator(), qmark='▶', amark='▶').execute()

		if select_channels == []:
			return

		threads = [Thread(target = self.current_guild.send_message_by_channel_id, args = (channel_id, message, tts, amount,)) for channel_id in select_channels]
		thread_runner(threads)

	def send_dms(self):
		dms, status = self.user.get_dms()
		dms_choices = [Choice(value = dm["id"], name = dm["recipients"][0]["username"] + "#" + dm["recipients"][0]["discriminator"]) for dm in dms]
		select_dms = inquirer.checkbox(message = "Select Dms:", choices = dms_choices, qmark='▶', amark='▶').execute()
		message = inquirer.text(message="Message:", qmark='▶', amark='▶').execute()
		amount = inquirer.number(message="Amount:", min_allowed=0, validate = EmptyInputValidator(), qmark='▶', amark='▶').execute()

		if select_dms == []:
			return

		threads = [Thread(target = self.user.send_dm_by_id, args = (dm_id, message, amount,)) for dm_id in select_dms]
		thread_runner(threads)

	def clear(self):
		os.system("cls") if os.name == "nt" else os.system("clear")

	def exit(self):
		__import__("os")._exit(1)