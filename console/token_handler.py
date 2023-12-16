__import__('sys').path.append("../")
import re
import sys
from InquirerPy import inquirer
from core.requester import Requester
from globals import logger, requester
from InquirerPy.base.control import Choice

class Action:
	LOAD_FROM_FILE = 0
	LOAD_FROM_INPUT = 1
	BACK = 2
	EXIT = 3

class TokenStatus:
	Vaild = 200
	Locked = 403
	Invalid = 401
	Unknown = 0

class TokenHandler:
	def __init__(self):
		self.token = None
		self.is_bot = None

	def _check_token_regex(self, token: str) -> bool:
		try:
			token_regex = r'[\w-]{24,26}.[\w-]{6}.[\w-]{27,38}'
			tokens = re.match(token_regex, token)
			res = True if tokens else False
			return res
		except:
			return False

	def _is_bot(self):
		token_type = inquirer.select(
				message = "Select Is Bot:",
				transformer = lambda select: f"[{select}]",
				choices = ["Bot", "User"],
				qmark='▶', amark='▶'
			).execute()
		return token_type

	def _check_token_status(self, token, token_type):
		global requester
		if requester == None:
			requester = Requester(9, token, token_type, logger)
		res, status = requester.api.get("users/@me")
		if status == TokenStatus.Vaild:
			return True
		else:
			return False

	def _load_token_from_file(self):
		with open("tokens.txt", "r") as f:
			tokens = f.readlines()
		hide_chars = 8
		tokens = [Choice(value = token.replace("\n", ""), name = token.replace("\n", "")[0:-hide_chars] + '*' * hide_chars) for token in tokens]
		tokens.append(Choice(value = Action.BACK, name = "Back"))
		self.token_type = self._is_bot()

		token = inquirer.select(
				message = "Select Token:",
				choices = tokens,
				transformer = lambda select: f"[hidden]" if select != "Back" else "[Back]",
				validate = lambda token: self._check_token_regex(token) and self._check_token_status(token, self.token_type) or token == Action.BACK, 
				invalid_message = "Invaild Token or Token!",
				qmark='▶', amark='▶'
			).execute()
		return token

	def _load_token_from_input(self):
		self.token_type = self._is_bot()
		token = inquirer.secret(message="Token:", transformer=lambda _: "[hidden]", validate = lambda token: self._check_token_regex(token), invalid_message = "Invaild Token!", qmark='▶', amark='▶').execute()
		return token

	def get_token(self):
		while True:
			load_method = inquirer.select(
					message="Select Method Load Token:",
					choices=[Choice(value = Action.LOAD_FROM_FILE, name = "Load From File"),
							Choice(value = Action.LOAD_FROM_INPUT, name = "Load From Input"),
							Choice(value = Action.EXIT, name = "Exit")
						],
						transformer=lambda select: f"[{select}]",
						default = Action.LOAD_FROM_FILE,
						qmark='▶', amark='▶'
				).execute()
			action = {
						Action.LOAD_FROM_FILE: self._load_token_from_file, 
						Action.LOAD_FROM_INPUT: self._load_token_from_input, 
						Action.EXIT: sys.exit
					}
			try:
				token = action[load_method]()
				if token == Action.BACK:
					continue
				return token, self.token_type
			except Exception as e:
				logger.error(e, True)
