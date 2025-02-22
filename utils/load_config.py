import os
import random
from itertools import cycle
from pathlib import Path
from typing import Optional, Union, Generator

import yaml
from loguru import logger
from better_proxy import Proxy

from models import Account, Config
from sys import exit


class ConfigurationError(Exception):
    """Base exception for configuration-related errors"""
    pass


class ConfigLoader:
    REQUIRED_PARAMS = frozenset({
        "cap_monster",
        "two_captcha",
        "capsolver",
        "referral_code",
        "threads"
    })

    def __init__(self, base_path: Union[str, Path] = None):
        self.base_path = Path(base_path or os.getcwd())
        self.config_path = self.base_path / "config"
        self.data_path = self.config_path / "data"
        self.settings_path = self.config_path / "settings.yaml"

    @staticmethod
    def _read_file(file_path: Path, allow_empty: bool = False) -> list[str]:
        if not file_path.exists():
            raise ConfigurationError(f"File not found: {file_path}")

        content = file_path.read_text(encoding='utf-8').strip()

        if not allow_empty and not content:
            raise ConfigurationError(f"File is empty: {file_path}")

        return [line.strip() for line in content.splitlines() if line.strip()]

    def _load_yaml(self) -> dict:
        try:
            config = yaml.safe_load(self.settings_path.read_text(encoding='utf-8'))
            missing_fields = self.REQUIRED_PARAMS - set(config.keys())

            if missing_fields:
                raise ConfigurationError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format: {e}")

    def _parse_proxies(self) -> Optional[list[Proxy]]:
        try:
            proxy_lines = self._read_file(self.data_path / "proxies.txt", allow_empty=False)
            for proxy in proxy_lines:
                Proxy.from_str(proxy)

            return [Proxy.from_str(proxy) for proxy in proxy_lines]
        except Exception as e:
            raise ConfigurationError(f"Failed to parse proxies: {e}")

    def _get_accounts(self) -> Generator[Account, None, None]:
        proxies = self._parse_proxies()
        proxy_cycle = cycle(proxies) if proxies else None

        wallets = self._read_file(self.data_path / "wallets.txt", allow_empty=False)

        try:
            auth_tokens = self._read_file(self.data_path / "auth_tokens.txt", allow_empty=True)
        except FileNotFoundError:
            auth_tokens = []
            

        for i, wallet in enumerate(wallets):
            try:
                auth_token = auth_tokens[i] if i < len(auth_tokens) else None

                yield Account(
                    pk_or_mnemonic=wallet,
                    proxy=next(proxy_cycle) if proxy_cycle else None,
                    auth_token=auth_token
                )
            except ValueError:
                logger.error(f"Failed to parse account: {wallet}")

    def load(self) -> Config | None:
        try:
            params = self._load_yaml()
            accounts = list(self._get_accounts())
            random.shuffle(accounts)

            return Config(
                accounts=accounts,
                **params
            )

        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            exit(1)


def load_config() -> Config:
    return ConfigLoader().load()