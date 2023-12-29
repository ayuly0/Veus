__import__('sys').path.append("../")
import asyncio
import aiohttp
from .api import API
from console.logger import Logger
from helpers.methods import get_proxies
from typing import Union

class Requester:

	def __init__(self, api_version: int, token: str, is_bot: bool,
	             logger: Logger):
		self.api = API(api_version, token, is_bot, logger)

	def set_token(self, token: str) -> None:
		self.api._token = token

	def handler_proxies(self, a, p):
		while len(p) < len(a) and p != None and type(p) != str:
			p += p
		p = [p] * len(a) if type(p) == str else p
		return p

	async def _get(self, path, proxies: Union[list, str, None] = None):
		async with aiohttp.ClientSession() as session:
			tasks = [self.api.aget(path, session, proxies)
			        ] if type(proxies) != list else [
			            self.api.aget(path, session, proxy) for proxy in proxies
			        ]
			return await asyncio.gather(*tasks)

	def get(self, path, proxies=None):
		return asyncio.run(self._get(path, proxies))

	async def _post(self, paths: Union[list, str, None], payloads, proxies):
		async with aiohttp.ClientSession() as session:
			if payloads == None:
				if type(paths) == list:
					proxies = self.handler_proxies(paths, proxies)
					tasks = [
					    self.api.apost(paths[i], payloads, session, proxies[i])
					    for i in len(range(paths))
					]
				else:
					tasks = [
					    self.api.apost(paths, payloads, session,
					                   proxies[len(proxies) // 2])
					]
			else:
				if type(paths) == list:
					proxies = self.handler_proxies(paths, proxies)
					tasks = [
					    self.api.apost(paths[i], payloads[i], session, proxies[i])
					    for i in range(len(paths))
					]
				else:
					proxies = self.handler_proxies(payloads, proxies)
					tasks = [
					    self.api.apost(paths, payloads[i], session, proxies[i])
					    for i in range(len(payloads))
					]
			return await asyncio.gather(*tasks)

	def post(self, path, payloads=None, proxies=None):
		proxies = get_proxies() if proxies == None else proxies
		return asyncio.run(self._post(path, payloads, proxies))

	async def _patch(self, paths, payloads, proxies):
		async with aiohttp.ClientSession() as session:
			if payloads == None:
				if type(paths) == list:
					proxies = self.handler_proxies(paths, proxies)
					tasks = [
					    self.api.apatch(paths[i], payloads, session, proxies[i])
					    for i in len(range(paths))
					]
				else:
					tasks = [
					    self.api.apatch(paths, payloads, session,
					                   proxies[len(proxies) // 2])
					]
			else:
				if type(paths) == list:
					proxies = self.handler_proxies(paths, proxies)
					tasks = [
					    self.api.apatch(paths[i], payloads[i], session, proxies[i])
					    for i in range(len(paths))
					]
				else:
					proxies = self.handler_proxies(payloads, proxies)
					tasks = [
					    self.api.apatch(paths, payloads[i], session, proxies[i])
					    for i in range(len(payloads))
					]
			return await asyncio.gather(*tasks)

	def patch(self, paths, payloads=None):
		proxies = get_proxies()
		return asyncio.run(self._patch(paths, payloads, proxies))

	async def _put(self, paths, payloads, proxies):
		async with aiohttp.ClientSession() as session:
			if payloads == None:
				if type(paths) == list:
					proxies = self.handler_proxies(paths, proxies)
					tasks = [
					    self.api.aput(paths[i], payloads, session, proxies[i])
					    for i in len(range(paths))
					]
				else:
					tasks = [
					    self.api.aput(paths, payloads, session,
					                   proxies[len(proxies) // 2])
					]
			else:
				if type(paths) == list:
					proxies = self.handler_proxies(paths, proxies)
					tasks = [
					    self.api.aput(paths[i], payloads[i], session, proxies[i])
					    for i in range(len(paths))
					]
				else:
					proxies = self.handler_proxies(payloads, proxies)
					tasks = [
					    self.api.aput(paths, payloads[i], session, proxies[i])
					    for i in range(len(payloads))
					]
			return await asyncio.gather(*tasks)

	def put(self, paths, payloads=None):
		proxies = get_proxies()
		return asyncio.run(self._put(paths, payloads, proxies))

	async def _delete(self, paths, payloads, proxies):
		async with aiohttp.ClientSession() as session:
			if payloads == None:
				if type(paths) == list:
					proxies = self.handler_proxies(paths, proxies)
					tasks = [
					    self.api.adelete(paths[i], payloads, session, proxies[i])
					    for i in len(range(paths))
					]
				else:
					tasks = [
					    self.api.adelete(paths, payloads, session,
					                   proxies[len(proxies) // 2])
					]
			else:
				if type(paths) == list:
					proxies = self.handler_proxies(paths, proxies)
					tasks = [
					    self.api.adelete(paths[i], payloads[i], session, proxies[i])
					    for i in range(len(paths))
					]
				else:
					proxies = self.handler_proxies(payloads, proxies)
					tasks = [
					    self.api.adelete(paths, payloads[i], session, proxies[i])
					    for i in range(len(payloads))
					]
			return await asyncio.gather(*tasks)

	def delete(self, paths, payloads=None):
		proxies = get_proxies()
		return asyncio.run(self._delete(paths, payloads, proxies))
