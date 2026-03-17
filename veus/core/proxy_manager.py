import random
from typing import Optional
from veus.console.logger import Logger

class ProxyManager:
    """Manages a pool of proxies with rotation and health tracking."""
    
    def __init__(self, logger: Logger, proxies: list[str] = None):
        self.logger = logger
        self._proxies: list[str] = proxies or []
        self._index = 0
        self._current_proxy: Optional[str] = None
        self._health: dict[str, int] = {p: 0 for p in self._proxies} # failures count
        self._max_failures = 3
        self.strategy = "round-robin"

    def add_proxies(self, proxies: list[str]):
        """Append new proxies to the pool."""
        for p in proxies:
            if p not in self._proxies:
                self._proxies.append(p)
                self._health[p] = 0

    def get_next(self, strategy: Optional[str] = None) -> Optional[str]:
        """Get the next proxy from the pool based on strategy."""
        current_strategy = strategy or self.strategy
        valid_proxies = [p for p in self._proxies if self._health.get(p, 0) < self._max_failures]
        
        if not valid_proxies:
            if self._proxies:
                self.logger.warn("All proxies in the pool have failed. Resetting health.")
                for p in self._proxies: self._health[p] = 0
                valid_proxies = self._proxies
            else:
                self._current_proxy = None
                return None

        if current_strategy == "random":
            self._current_proxy = random.choice(valid_proxies)
        else:
            # Round-robin
            self._current_proxy = valid_proxies[self._index % len(valid_proxies)]
            self._index += 1
            
        return self._current_proxy

    def get_current(self) -> str:
        """Return current proxy or Direct."""
        return self._current_proxy or "Direct"

    def mark_failed(self, proxy: str):
        """Track failures for a proxy."""
        if proxy in self._health:
            self._health[proxy] += 1
            if self._health[proxy] >= self._max_failures:
                self.logger.error(f"Proxy {proxy} blacklisted after {self._max_failures} failures.")

    def mark_success(self, proxy: str):
        """Reset failure count on success."""
        if proxy in self._health:
            self._health[proxy] = 0

    @property
    def total_count(self) -> int:
        return len(self._proxies)

    @property
    def healthy_count(self) -> int:
        return len([p for p in self._proxies if self._health.get(p, 0) < self._max_failures])
