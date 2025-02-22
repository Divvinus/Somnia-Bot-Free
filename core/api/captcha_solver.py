import asyncio
import json

from typing import  Any
from better_proxy import Proxy
from loguru import logger

from loader import config
from .base_client import BaseAPIClient


class CapcthaSolutionWorker(BaseAPIClient):
    def __init__(self, proxy: Proxy = None):
        super().__init__(base_url="", proxy=proxy)
        self.api_key: str = ""

    @staticmethod
    def _check_available_api_key():
        list_api_key = [config.cap_monster, config.two_captcha, config.capsolver]
        list_available_api_key = list(filter(None, list_api_key))
        if not list_available_api_key: return None
        else: return list_available_api_key

    async def _check_balance_api_key(self, api_key):
        if api_key == config.cap_monster: self.base_url = "https://api.capmonster.cloud"
        elif api_key == config.two_captcha: self.base_url = "https://api.2captcha.com"
        elif api_key == config.capsolver: self.base_url = "https://api.capsolver.com"
        json_data = {
            "clientKey": api_key
        }
        response: str = await self.send_request(request_type="POST", method="/getBalance", json_data=json_data, verify=False)
        response_dict = json.loads(response)
        if response_dict.get("balance") is None or response_dict.get("balance") == 0: return False
        return True

    async def _get_available_api_key(self):
        list_api_key = self._check_available_api_key()

        if list_api_key is None: return False, "Could not find api key to solve captcha"

        for api_key in list_api_key:
            balance = await self._check_balance_api_key(api_key)
            if balance: return api_key, "OK"

        return False, "All available api keys for solving captcha are unbalanced"

    async def _create_task(self, website_url: str, website_key: str) -> dict:
        type_request = "AntiTurnstileTaskProxyLess" if self.api_key == config.capsolver else "TurnstileTaskProxyless"

        json_data = {
            "clientKey": self.api_key,
            "task": {
                "type": type_request,
                "websiteURL": website_url,
                "websiteKey": website_key
            }
        }

        response: str = await self.send_request(method="/createTask", json_data=json_data, verify=False)
        data = json.loads(response)
        return data.get("taskId")

    async def get_task_result(self, website_url: str, website_key: str, start_attempt: int = 0, finish_attempt: int = 60) -> None | tuple[bool, Any] | tuple[bool, str]:
        self.api_key, message = await self._get_available_api_key()
        if not self.api_key: return False, message
        while True:
            try:
                task_id = await self._create_task(website_url, website_key)
                if not task_id: continue

                while start_attempt <= finish_attempt:
                    json_data = {
                        "clientKey": self.api_key,
                        "taskId": task_id
                    }

                    response: dict = await self.send_request(method="/getTaskResult", json_data=json_data)

                    if not isinstance(response, dict): break

                    status = response.get("status")

                    if status == "processing":
                        await asyncio.sleep(2)
                        continue

                    if response.get("errorId") == 12: break

                    if status == "ready" and "solution" in response:
                        return True, response["solution"]["token"]

            except Exception as error:
                logger.error(f"Error during captcha solving: {error}")
                await asyncio.sleep(5)

            return False, "Failed to solve captcha after maximum attempts"