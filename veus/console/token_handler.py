import re
import os
from typing import Optional
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from veus.console.logger import Logger
from veus.core.requester import Requester

class TokenHandler:
    """Handles token acquisition and validation."""
    
    def __init__(self, logger: Logger):
        self.logger = logger

    def _validate_regex(self, token: str) -> bool:
        # Basic Discord token regex
        regex = r'[\w-]{24,26}\.[\w-]{6}\.[\w-]{27,38}'
        return bool(re.match(regex, token))

    async def _check_status(self, token: str, is_bot: bool, verify: bool = True) -> bool:
        """Verify token with Discord API."""
        # Temporary requester just for validation
        rq = Requester(token, is_bot, self.logger, verify=verify)
        try:
            _, status = await rq.api.get("users/@me", silent=True)
            return status == 200
        finally:
            await rq.shutdown()

    async def setup_session(self, config) -> tuple[str, bool, bool, list[str]]:
        """Consolidated 'Landing Zone' for professional session setup."""
        while True:
            choice = await inquirer.select(
                message="Select Session Entry Type:",
                choices=[
                    Choice("direct", "Standard Direct (Unobfuscated)"),
                    Choice("proxy", "Secure Tunnel (proxies.txt + SSL Bypass)"),
                    Choice("vault", "Identity Vault (tokens.txt)"),
                    Choice("exit", "Exit Application")
                ],
                pointer="▶"
            ).execute_async()

            if choice == "exit":
                os._exit(0)

            # 1. Determine Proxy & SSL Needs
            use_proxies = choice == "proxy"
            verify_ssl = config.get("ssl_verify", True)
            
            # Special case for Proxy Tunnel: usually implies FlareTunnel/Insecure
            if use_proxies and verify_ssl:
                if await inquirer.confirm(message="Skip SSL verification (Recommended for some proxies)?", default=True).execute_async():
                    verify_ssl = False

            # 2. Get Proxies
            proxies = []
            if use_proxies:
                if not os.path.exists("proxies.txt"):
                    self.logger.error("proxies.txt not found!")
                    continue
                with open("proxies.txt", "r") as f:
                    proxies = [l.strip() for l in f if l.strip()]
                self.logger.info(f"Initialized tunnel with {len(proxies)} proxies.")

            # 3. Get Token
            method = choice if choice == "vault" else "input"
            is_bot = await inquirer.confirm(message="Is this a Bot token?", default=False).execute_async()
            
            token = ""
            if method == "input" or choice == "proxy":
                token = await inquirer.secret(
                    message="Enter Token:",
                    validate=self._validate_regex,
                    invalid_message="Invalid format."
                ).execute_async()
            else: # Vault
                if not os.path.exists("tokens.txt"):
                    self.logger.error("tokens.txt not found!")
                    continue
                with open("tokens.txt", "r") as f:
                    lines = [l.strip() for l in f if l.strip()]
                if not lines:
                    self.logger.error("tokens.txt is empty!")
                    continue
                token = await inquirer.select(
                    message="Select Identity:",
                    choices=[Choice(t, f"{t[:10]}...{t[-5:]}") for t in lines]
                ).execute_async()

            # 4. Final Validation
            with self.logger.yaspin(text="Validating identity...", color="yellow"):
                if await self._check_status(token, is_bot, verify=verify_ssl):
                    return token, is_bot, verify_ssl, proxies
                
            self.logger.error("Access denied: Invalid or expired token.")
