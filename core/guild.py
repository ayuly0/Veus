__import__('sys').path.append('../')
from helpers.methods import split_list, thread_runner
from threading import Thread

class Guilds:
	def __init__(self, requester: object, logger: object):
		self.rq = requester
		self.logger = logger
		self._guilds_info, status = self.rq.get(path = "users/@me/guilds")[0]
		self.guild_ids = {
			int(guild["id"]): guild["name"] for guild in self._guilds_info
		}
		self.loaded_guilds = {}

	def load_guild(self, guild_id: int) -> None:
		self.loaded_guilds[guild_id] = Guild(self.rq, self.logger, guild_id)

class ChannelTypes:
	GUILD_TEXT = 0
	DM = 1
	GUILD_VOICE = 2
	GROUP_DM = 3
	GUILD_CATEGORY = 4
	GUILD_ANNOUNCEMENT = 5
	ANNOUNCEMENT_THREAD = 10
	PUBLIC_THREAD = 11
	PRIVATE_THREAD = 12
	GUILD_STAGE_VOICE = 13
	GUILD_DIRECTORY = 14
	GUILD_FORUM	 = 15
	GUILD_MEDIA = 16

class Guild:
	def __init__(self, requester: object, logger: object, guild_id: int):
		self.rq = requester
		self.logger = logger
		self.guild_id = guild_id
		self.guild_info, status = self.rq.get(path = f"guilds/{self.guild_id}")[0]
		if status != 200:
			return
		
		# extract info of server #
		self.name = self.guild_info["name"]
		self.description = self.guild_info["description"]
		self.max_members = self.guild_info["max_members"]
		self.owner_id = self.guild_info["owner_id"]
		self.user_id = self.rq.get("users/@me")[0][0]["id"]
		self.is_owner = self.owner_id == self.user_id

	def __str__(self) -> str:
		return f"Guild(id={self.guild_id}, name={self.name})"

	def __repr__(self) -> str:
		return f"Guild(id={self.guild_id}, name={self.name})"

	def _route(self, path: str) -> str:
		return  f"guilds/{self.guild_id}/{path}"

	def get_all_channels(self) -> tuple:
		return self.rq.get(self._route("channels"))[0]

	def get_all_roles(self) -> tuple:
		return self.rq.get(self._route("roles"))[0]

	def get_all_users(self) -> tuple:
		response, status_code = self.rq.get(self._route("members?limit=1000"))[0]
		if status_code != 200:
			return response, status_code

		users_id = [[user["user"]["id"], user["user"]["username"]] for user in response]
		return users_id

	def get_all_emojis(self) -> tuple:
		return self.rq.get(self._route("emojis"))[0]

	def get_all_webhooks(self) -> tuple:
		return self.rq.get(self._route("webhooks"))[0]

	def change_guild_name(self, new_name: str) -> tuple:
		payload = {
			"name": new_name
		}
		return self.rq.patch(f"guilds/{self.guild_id}", [payload])[0]

	def change_guild_icon(self, icon: str) -> tuple:
		payload = {
			"icon": icon
		}
		return self.rq.patch(f"guilds/{self.guild_id}", [payload])

	def send_webhook_message(self, webhhok_id: int, webhook_token: str, message: str, tts: bool = False) -> tuple:
		payload = {
			"content": message,
			"tts": tts
		}
		return self.rq.post(f"webhooks/{webhhok_id}/{webhook_token}", [payload])

	def send_message(self, channel_id: int, message: str, tts: bool = False, amount: int = 1) -> tuple:
		payload = {
			"content": message,
			"tts": int(tts)
		}
		payloads = [payload for i in range(int(amount))]
		sl = split_list(payloads, 10)
		threads = [Thread(target = self.rq.post, args = (f"channels/{channel_id}/messages", payloads,)) for payloads in sl]
		thread_runner(threads)
		# return self.rq.post(f"channels/{channel_id}/messages", payloads)

	def create_webhook(self, channel_id: int, name: str, avatar: str = None) -> tuple:
		payload = {
			"name": name,
			"avatar": avatar
		}
		return self.rq.post(f"channels/{channel_id}/webhooks", [payload])[0]

	def create_roles(self, name: str, permissions: int = 0, color: int = 0, amount: int = 1) -> tuple:
		payload = {
			"name": name,
			"color": color,
			"permissions": permissions
		}
		return self.rq.post(self._route("roles"), [payload for i in range(int(amount))])

	def create_channels(self, name: str, channel_type: int = ChannelTypes.GUILD_TEXT, amount: int = 1) -> tuple:
		payload = {
			"name": name,
			"type": channel_type
		}
		paths = [self._route("channels") for i in range(int(amount))]
		payloads = [payload for i in range(int(amount))]
		sl = split_list(payloads, 10)
		threads = [Thread(target = self.rq.post, args = (self._route("channels"), payloads,)) for payloads in sl]
		thread_runner(threads)
		# return self.rq.post(paths, payloads)

	def delete_channel_by_id(self, channel_id: int) -> tuple:
		return self.rq.delete([f"channels/{channel_id}"])

	def delete_all_channels(self) -> tuple:
		channels, status = self.get_all_channels()
		channels_path = [f"channels/{channel['id']}" for channel in channels]
		return self.rq.delete(channels_path)

	def delete_channels(self, channel_ids: list) -> tuple:
		self.rq.delete([f"channels/{channel_id}" for channel_id in channels_ids])

	def delete_emoji_by_id(self, emoji_id: int) -> tuple:
		return self.rq.delete([self._route(f"emojis/{emoji_id}")])[0]

	def delete_all_emojis(self) -> tuple:
		emojis, status = self.get_all_emojis()
		emoji_paths = [self._route(f"emojis/{emoji['id']}") for emoji in emojis]
		return self.rq.delete(emoji_paths)

	def delete_role_by_id(self, role_id: int) -> tuple:
		return self.rq.post(f"roles/{role_id}")

	def delete_all_roles(self) -> tuple:
		roles, status = self.get_all_roles()
		role_paths = []
		for role in roles:
			if role["name"] == "everyone":
				continue
			role_paths.append(self._route(f"roles/{role['id']}"))
		sl = split_list(role_paths, 5)
		threads = [Thread(target = self.rq.delete, args = (role_paths,)) for role_paths in sl]
		thread_runner(threads)

	def kick_user_by_id(self, user_id: int) -> tuple:
		return self.rq.delete([self._route(f"members/{user_id}")])[0]

	def kick_all_users(self) -> tuple:
		users = self.get_all_users()
		kick_paths = [self._route(f"members/{user[0]}") for user in users]
		return self.rq.delete(kick_paths)

	def ban_user_by_id(self, user_id: int) -> tuple:
		payload = {
			"delete_message_days": 0,
			"reason": "by Veus"
		}
		return self.rq.put(f"bans/{user_id}", [payload])[0]

	def ban_all_users(self) -> tuple:
		payload = {
			"delete_message_days": 0,
			"reason": "by Veus"
		}
		users = self.get_all_users()
		ban_paths = [self._route(f"bans/{user[0]}") for user in users]
		return self.rq.put(ban_paths, [payload])

	def leave_guild(self) -> None:
		if self.is_owner:
			self.logger.warn(f"User is owner of {self.name} guild!")
			return None
		payload = {
			'lurking': False
		}
		res, status = self.rq.delete([f"users/@me/guilds/{self.guild_id}"], [payload])[0]
		self.logger.debug(res)
		self.logger.success(f"Leave {self.name} guild.") if status == 204 else	self.logger.fail(f"Leave {self.name} guild.")

	def delete_guild(self) -> None:
		if not self.is_owner:
			self.logger.warn(f"User is not owner of {self.name} guild!")
			return None
		res, status = self.rq.post([f"users/@me/guilds/{self.guild_id}/delete"])
		self.logger.debug(res)
		self.logger.success(f"Delete {self.name} guild.") if status == 204 else	self.logger.fail(f"Delete {self.name} guild.")
