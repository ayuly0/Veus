__import__('sys').path.append("../")
from .guild import Guilds
from console.logger import Logger

class User:
	def __init__(self, requester: object):
		self.rq = requester
		self.logger = Logger(debug = True)
		self.guilds = Guilds(self.rq, self.logger)
		self.get_user_info()
		self.username = f"{self.username}#{self.discriminator}"
		self.logger.set_username(self.username)

		self.rq.logger = self.logger

	def __str__(self) -> str:
		return f"User(id={self.user_id}, username={self.username}#{self.discriminator})"

	def __repr__(self) -> str:
		return f"User(id={self.user_id}, username={self.username}#{self.discriminator})"

	def get_user_info(self) -> dict:
		self.user_info, status = self.rq.get("users/@me")[0]

		self.user_id = self.user_info["id"]
		self.username = self.user_info["username"]
		self.discriminator = self.user_info["discriminator"]
		self.global_name = self.user_info["global_name"]
		self.premium_type = self.user_info["premium_type"]
		self.mfa_enabled = self.user_info["mfa_enabled"]
		self.locale = self.user_info["locale"]
		self.email = self.user_info["email"]
		self.verified = self.user_info["verified"]
		self.bio = self.user_info["bio"]
		return self.user_info

	def update_profile(self, new_bio: str, new_pronous: str) -> tuple:
		payload = {
			'bio': new_bio
		}
		res, status = self.rq.patch("users/@me/profile", [payload])[0]
		if status == 204:
			self.logger.success(f"Update bio to {new_bio}")
		else:
			self.logger.fail(f"Update bio to {new_bio}")
			self.logger.info(res["message"])
		return res

	def update_global_name(self, new_global_name: str) -> tuple:
		pass

	def update_settings(self) -> tuple:
		pass

	def send_dm_message(self, channel_id: int, message: str, amount: int = 1) -> tuple:
		payload = {
			"content": message,
		}
		payloads = [payload for i in range(int(amount))]
		return self.rq.post(f"channels/{channel_id}/messages", payloads)

	def block_friend_by_id(self, user_id: int) -> tuple:
		pass

	def block_friends(self) -> tuple:
		pass

	def close_dm_by_id(self, dm_id: int) -> tuple:
		pass

	def close_dms(self) -> tuple:
		pass

	def unfriend_by_id(self, user_id: int) -> tuple:
		pass

	def unfriends(self) -> tuple:
		pass