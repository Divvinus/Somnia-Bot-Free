import asyncio
import json
import random
import time
from typing import Literal, Optional
from dataclasses import dataclass

from better_proxy import Proxy
from curl_cffi.requests import AsyncSession

from core.exceptions.base import APIError, SessionRateLimited, ServerError

@dataclass
class ChromeVersion:
    version: str
    weight: int
    ua_version: str

class ProxyLocale:
    COUNTRY_LOCALES = {
        'DE': 'de-DE,de;q=0.9,en;q=0.8',
        'GB': 'en-GB,en;q=0.9',
        'FR': 'fr-FR,fr;q=0.9,en;q=0.8',
        'IT': 'it-IT,it;q=0.9,en;q=0.8',
        'ES': 'es-ES,es;q=0.9,en;q=0.8',
        'US': 'en-US,en;q=0.9',
        'CA': 'en-CA,en;q=0.9,fr-CA;q=0.8',
        'JP': 'ja-JP,ja;q=0.9,en;q=0.8',
        'KR': 'ko-KR,ko;q=0.9,en;q=0.8',
        'DEFAULT': 'en-US,en;q=0.9'
    }

    @classmethod
    def get_locale_for_proxy(cls, proxy: Optional[Proxy]) -> str:
        return cls.COUNTRY_LOCALES['DEFAULT']

class BrowserProfile:
    CHROME_VERSIONS = [
        ChromeVersion("chrome119", 5, "119.0.0.0"),
        ChromeVersion("chrome120", 10, "120.0.0.0"),
        ChromeVersion("chrome123", 15, "123.0.0.0"),
        ChromeVersion("chrome124", 20, "124.0.0.0"),
    ]

    @classmethod
    def get_random_chrome_version(cls) -> ChromeVersion:
        versions = [v for v in cls.CHROME_VERSIONS]
        weights = [v.weight for v in versions]
        return random.choices(versions, weights=weights, k=1)[0]

class BaseAPIClient:
    def __init__(self, 
                 base_url: str, 
                 proxy: Optional[Proxy] = None,
                 session_lifetime: int = 5,
                 enable_random_delays: bool = True):
        self.base_url = base_url
        self.proxy = proxy
        self.session_lifetime = session_lifetime
        self.enable_random_delays = enable_random_delays
        self.requests_count = 0
        self.last_url = None
        self.session_start_time = None
        self.session = self._create_session()

    def _create_session(self) -> AsyncSession:
        chrome_version = BrowserProfile.get_random_chrome_version()
        
        session = AsyncSession(
            impersonate=chrome_version.version,
            verify=False,
            timeout=random.uniform(25, 35)
        )

        locale = ProxyLocale.get_locale_for_proxy(self.proxy)
        
        windows_ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version.ua_version} Safari/537.36"
        
        session.headers.update({
            "Accept-Language": locale,
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": windows_ua,
            "sec-ch-ua": f'"Chromium";v="{chrome_version.ua_version.split(".")[0]}", "Google Chrome";v="{chrome_version.ua_version.split(".")[0]}", "Not=A?Brand";v="99"',
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-mobile": "?0"
        })

        if self.proxy:
            session.proxies = {
                "http": self.proxy.as_url,
                "https": self.proxy.as_url,
            }

        self.session_start_time = time.time()
        return session

    async def _manage_cookies(self, response):
        if response.cookies:
            if random.random() < 0.1:
                current_time = time.time()
                old_cookies = {
                    k: v for k, v in self.session.cookies.items()
                    if current_time - self.session_start_time > 3600
                }
                for key in old_cookies:
                    del self.session.cookies[key]

            self.session.cookies.update(response.cookies)

    async def _add_random_delay(self):
        if self.enable_random_delays:
            delay = abs(random.gauss(1.5, 0.5))
            delay += random.random() * 0.1
            await asyncio.sleep(delay)

    async def _maybe_rotate_session(self):
        self.requests_count += 1
        actual_lifetime = self.session_lifetime * random.uniform(0.8, 1.2)
        if self.requests_count >= actual_lifetime:
            await self.session.close()
            self.session = self._create_session()
            self.requests_count = 0

    async def send_request(
        self,
        request_type: Literal["POST", "GET", "OPTIONS", "PATCH"] = "POST",
        method: str = None,
        json_data: dict = None,
        params: dict = None,
        url: str = None,
        headers: dict = None,
        cookies: dict = None,
        verify: bool = True,
        max_retries: int = 3,
        retry_delay: float = 3.0,
        allow_redirects: bool = False,
    ):
        url = url if url else f"{self.base_url}{method}"
        await self._maybe_rotate_session()
        await self._add_random_delay()

        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)

        if self.last_url and not url.startswith(self.last_url):
            request_headers["Referer"] = self.last_url

        for attempt in range(max_retries):
            try:
                if request_type == "POST":
                    response = await self.session.post(
                        url,
                        json=json_data,
                        params=params,
                        headers=request_headers,
                        cookies=cookies,
                        allow_redirects=allow_redirects,
                    )
                elif request_type == "PATCH":   
                    response = await self.session.patch(
                        url,
                        json=json_data,
                        params=params,
                        headers=request_headers,
                        cookies=cookies,
                        allow_redirects=allow_redirects,
                    )
                elif request_type == "OPTIONS":
                    response = await self.session.options(
                        url,
                        headers=request_headers,
                        cookies=cookies,
                        allow_redirects=allow_redirects,
                    )
                else:
                    response = await self.session.get(
                        url,
                        params=params,
                        headers=request_headers,
                        cookies=cookies,
                        allow_redirects=allow_redirects,
                    )

                await self._manage_cookies(response)
                self.last_url = url

                if verify:
                    if response.status_code == 403:
                        raise SessionRateLimited("Session is rate limited")

                    if response.status_code in (500, 502, 503, 504):
                        raise ServerError(f"Server error - {response.status_code}")

                return response

            except Exception as error:
                if attempt == max_retries - 1:
                    raise error
                await asyncio.sleep(retry_delay * (2 ** attempt))

        raise ServerError(f"Failed to send request after {max_retries} attempts")

    @staticmethod
    async def _verify_response(response_data: dict | list):
        if isinstance(response_data, dict):
            if "status" in str(response_data):
                if isinstance(response_data, dict):
                    if response_data.get("status") is False:
                        raise APIError(
                            f"API returned an error: {response_data}", response_data
                        )
                    elif response_data.get("status", "").lower() == "failed":
                        raise APIError(
                            f"API returned an error: {response_data}", response_data
                        )
            elif "success" in str(response_data):
                if isinstance(response_data, dict):
                    if response_data.get("success") is False:
                        raise APIError(
                            f"API returned an error: {response_data}", response_data
                        )
            elif "error" in str(response_data):
                raise APIError(
                    f"API returned an error: {response_data}", response_data
                )
            elif "statusCode" in str(response_data):
                if response_data.get("statusCode", 0) not in (200, 201, 202, 204):
                    raise APIError(
                        f"API returned an error: {response_data}", response_data
                        )