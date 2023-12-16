import asyncio
import aiohttp
from .api import API

class Requester:
	def __init__(self, api_version: int, token: str, token_type: str, logger: object):
		self.api = API(api_version, token, token_type, logger)

	def set_token(self, token: str) -> None:
		self.api._token = token

	async def _get(self, path, proxies = None):
		async with aiohttp.ClientSession() as session:
			tasks = [self.api.aget(path, session, proxies)] if type(proxies) != list else [self.api.aget(path, session, proxy) for proxy in proxies]
			return await asyncio.gather(*tasks)

	def get(self, path, proxies = None):
		return asyncio.run(self._get(path, proxies))

	async def _post(self, paths, payloads, proxy):
		async with aiohttp.ClientSession() as session:
			if payloads == None:
				if type(paths) == list:
					tasks = [self.api.apost(path, payloads, session, proxy) for path in paths]
				else:
					tasks = [self.api.apost(paths, payloads, session, proxy)]
			else:
				if type(paths) == list:
					tasks = [self.api.apost(paths[i], payloads[i], session, proxy) for i in range(len(paths))]
				else:
					tasks = [self.api.apost(paths, payload, session, proxy) for payload in payloads]
			return await asyncio.gather(*tasks)

	def post(self, path, payloads = None, proxies = None):
		return asyncio.run(self._post(path, payloads, proxies))

	async def _patch(self, paths, payloads, proxy):
		async with aiohttp.ClientSession() as session:
			if payloads == None:
				if type(paths) == list:
					tasks = [self.api.apatch(path, payloads, session, proxy) for path in paths]
				else:
					tasks = [self.api.apatch(paths, payloads, session, proxy)]
			else:
				if type(paths) == list:
					tasks = [self.api.apatch(paths[i], payloads[i], session, proxy) for i in range(len(paths))]
				else:
					tasks = [self.api.apatch(paths, payload, session, proxy) for payload in payloads]
			return await asyncio.gather(*tasks)

	def patch(self, paths, payloads = None, proxy = None):
		return asyncio.run(self._patch(paths, payloads, proxy))

	async def _put(self, paths, payloads, proxy):
		async with aiohttp.ClientSession() as session:
			if payloads == None:
				if type(paths) == list:
					tasks = [self.api.aput(path, payloads, session, proxy) for path in paths]
				else:
					tasks = [self.api.aput(paths, payloads, session, proxy)]
			else:
				if type(paths) == list:
					tasks = [self.api.aput(paths[i], payloads[i], session, proxy) for i in range(len(paths))]
				else:
					tasks = [self.api.aput(paths, payload, session, proxy) for payload in payloads]
			return await asyncio.gather(*tasks)

	def put(self, paths, payloads = None, proxy = None):
		return asyncio.run(self._put(paths, payloads, proxy))

	async def _delete(self, paths, payloads, proxy):
		async with aiohttp.ClientSession() as session:
			if payloads == None:
				if type(paths) == list:
					tasks = [self.api.adelete(path, session, payloads, proxy) for path in paths]
				else:
					tasks = [self.api.adelete(paths, session, payloads, proxy)]
			else:
				if type(paths) == list:
					tasks = [self.api.adelete(paths[i], session, payloads[i], proxy) for i in range(len(paths))]
				else:
					tasks = [self.api.adelete(paths, session, payload, proxy) for payload in payloads]
			return await asyncio.gather(*tasks)

	def delete(self, paths, payloads = None, proxy = None):
		return asyncio.run(self._delete(paths, payloads, proxy))
