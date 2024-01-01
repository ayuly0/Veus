import time
import json
import requests
import async_timeout

# from stem import Signal
from typing import Union, Any

# from stem.control import Controller

__import__("sys").path.append("../")
from console.logger import Logger


class API:
	def __init__(
		self, api_version: int, token: str, is_bot: bool, logger: Logger
	) -> None:
		self._api_version = api_version
		self._token = token
		self.logger = logger
		self._header = {"Authorization": f"{'Bot ' if is_bot else ''}{self._token}"}
		self._api_url = f"https://discord.com/api/v{self._api_version}"

	def _route(self, api_path: str) -> str:
		return f"{self._api_url}/{api_path}"

	def _logger(self, _type, message):
		if _type == "info":
			self.logger.info(message)
		elif _type == "success":
			self.logger.success(message)
		elif _type == "warn":
			self.logger.warn(message)
		elif _type == "error":
			self.logger.error(message, True)
		elif _type == "debug":
			self.logger.debug(message)

	# ------[Async Requests]------ #

	async def aget(
		self, api_path: str, session, proxy: Union[str, Any] = None
	) -> tuple:
		url = self._route(api_path)
		try:
			async with async_timeout.timeout(360):
				async with session.get(
					url, headers=self._header, proxy=proxy
				) as response:
					return await response.json(content_type=None), response.status
		except Exception as ex:
			self._logger("error", ex)
			return ()

	async def apost(
		self, api_path: str, payload: dict, session, proxy: str = ""
	) -> tuple:
		url = self._route(api_path)
		while True:
			try:
				async with async_timeout.timeout(360):
					async with session.post(
						url, json=payload, headers=self._header, proxy=proxy
					) as response:
						if response.status == 429:
							res = await response.json(content_type=None)
							self.logger.debug(res)
							self.logger.warn(
								f"Rate limit! Retry after {res['retry_after']}s."
							)
							time.sleep(res["retry_after"])
							# with Controller.from_port(port=9051) as controller:
							# 	controller.authenticate(password="somepass")
							# 	controller.signal(Signal.NEWNYM)
						else:
							return (
								await response.json(content_type=None),
								response.status,
							)
			except Exception as ex:
				if all(
					[
						"10054" not in str(ex),
						"10053" not in str(ex),
						"Cannot connect" not in str(ex),
						"Expecting value: line 1" not in str(ex),
						"503" not in str(ex),
						"Server disconnected" not in str(ex),
					]
				):
					self._logger("error", ex)
					return ()

	async def apatch(
		self, api_path: str, payload: dict, session, proxy: str = ""
	) -> tuple:
		url = self._route(api_path)
		while True:
			try:
				async with async_timeout.timeout(360):
					async with session.patch(
						url, json=payload, headers=self._header, proxy=proxy
					) as response:
						if response.status == 429:
							res = await response.json(content_type=None)
							self.logger.debug(res)
							self.logger.warn(
								f"Rate limit! Retry after {res['retry_after']}s."
							)
							time.sleep(res["retry_after"])
						else:
							return (
								await response.json(content_type=None),
								response.status,
							)
			except Exception as ex:
				if "10054" not in str(ex) or "10053" not in str(ex):
					self._logger("error", ex)
					return ()

	async def aput(
		self, api_path: str, payload: dict, session, proxy: str = ""
	) -> tuple:
		url = self._route(api_path)
		while True:
			try:
				async with async_timeout.timeout(360):
					async with session.put(
						url, json=payload, headers=self._header, proxy=proxy
					) as response:
						if response.status == 429:
							res = await response.json(content_type=None)
							self.logger.debug(res)
							self.logger.warn(
								f"Rate limit! Retry after {res['retry_after']}s."
							)
							time.sleep(res["retry_after"])
						else:
							return (
								await response.json(content_type=None),
								response.status,
							)
			except Exception as ex:
				if "10054" not in str(ex) or "10053" not in str(ex):
					self._logger("error", ex)
					return ()

	async def adelete(
		self, api_path: str, proxy: str = "", session=None, payload: dict = {}
	) -> tuple:
		url = self._route(api_path)
		while True:
			try:
				async with async_timeout.timeout(360):
					async with session.delete(
						url, json=payload, headers=self._header, proxy=proxy
					) as response:
						res = await response.json(content_type=None)
						self.logger.debug(res)
						if response.status == 429:
							self.logger.warn(
								f"Rate limit! Retry after {res['retry_after']}s."
							)
							time.sleep(res["retry_after"])
						else:
							return res, response.status
			except Exception as ex:
				if "10054" not in str(ex) or "10053" not in str(ex):
					self._logger("error", ex)
					return ()

	# ------[Normal Requests]------ #

	def get(self, api_path: str) -> tuple[Any, Any]:
		url = self._route(api_path)

		response = requests.get(url, headers=self._header)
		return json.loads(response.text), response.status_code

	def post(self, api_path: str, payload: dict) -> tuple[Any, Any]:
		url = self._route(api_path)

		response = requests.post(url, json=payload, headers=self._header)
		return json.loads(response.text), response.status_code

	def patch(self, api_path: str, payload: dict) -> tuple[Any, Any]:
		url = self._route(api_path)

		response = requests.patch(url, json=payload, headers=self._header)
		return json.loads(response.text), response.status_code

	def put(self, api_path: str, payload: dict) -> tuple[Any, Any]:
		url = self._route(api_path)

		response = requests.patch(url, json=payload, headers=self._header)
		return json.loads(response.text), response.status_code

	def delete(self, api_path: str, payload: dict) -> tuple[Any, Any]:
		url = self._route(api_path)

		response = requests.delete(url, json=payload, headers=self._header)
		return json.loads(response.text), response.status_code
