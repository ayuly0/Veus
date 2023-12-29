import asyncio
import aiohttp
import async_timeout
import threading
from .methods import split_list, thread_runner

class ProxiesChecker:
	def __init__(self, save_to_file: bool = True):
		self.save_to_file = save_to_file
		self.good_proxies = []

	async def _check_proxies(self, proxies: list) -> None:
		async with aiohttp.ClientSession() as session:
			tasks = [self.check_proxy(proxy, session) for proxy in proxies]
			return await asyncio.gather(*tasks)

	async def check_proxy(self, proxy: str, session) -> None:
		while True:
			try:
				async with async_timeout.timeout(360):
					async with session.get("http://api.ipify.org", proxy=proxy) as response:
						res = await response.text()
						if res != proxy:
							# print(f"[-] {proxy}")
							return ""
						print(f"[+] {proxy}")
						return proxy
			except Exception as ex:
				# print(f"[ERR] [{proxy}] {ex}")
				return ex

	def check_proxies(self, proxies: list) -> None:
		self.good_proxies = asyncio.run(self._check_proxies(proxies))

	def check_proxies_thread(self, proxies: list, proxy_per_thread: int = 10) -> None:
		sl = split_list(proxies, proxy_per_thread)
		threads = [threading.Thread(target = self.check_proxies, args = (proxies,)) for proxies in sl]
		thread_runner(threads)