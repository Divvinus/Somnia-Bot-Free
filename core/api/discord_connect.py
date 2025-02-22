from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse
from better_proxy import Proxy

from core.api import BaseAPIClient
from models import Account

class DiscordConnectModule(BaseAPIClient):
    def __init__(self, account: Account):
        self.token = account.token_discord
        self.proxy = account.proxy
        
        super().__init__(
            base_url="https://discord.com",
            proxy=self.proxy,
            session_lifetime=5,
            enable_random_delays=True
        )
        
        self.auth_headers = self._build_auth_headers()

    def _build_auth_headers(self) -> Dict[str, str]:
        """Создаем заголовки для авторизации в Discord"""
        chrome_version = self.session.headers['sec-ch-ua'].split('"')[3]
        return {
            'authority': 'discord.com',
            'accept': '*/*',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
            'authorization': self.token,
            'user-agent': self.session.headers['User-Agent'],
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'ru',
            'x-discord-timezone': 'Europe/Vilnius',
            'sec-ch-ua': f'"Google Chrome";v="{chrome_version}", "Not=A?Brand";v="8", "Chromium";v="{chrome_version}"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InJ1IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyOS4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTI5LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiJodHRwczovL2Rpc2NvcmQuY29tL2FwcC9pbnZpdGUtd2l0aC1ndWlsZC1vbmJvYXJkaW5nL2lua29uY2hhaW4iLCJyZWZlcnJpbmdfZG9tYWluIjoiZGlzY29yZC5jb20iLCJyZWZlcnJlcl9jdXJyZW50IjoiaHR0cHM6Ly9xdWVzdC5zb21uaWEubmV0d29yay8iLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiJxdWVzdC5zb21uaWEubmV0d29yayIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjM3MDUzMywiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbCwiaGFzX2NsaWVudF9tb2RzIjpmYWxzZX0='
        }

    async def _request_authorization(self) -> str:
        params = {
            'client_id': '1318915934878040064',
            'response_type': 'code',
            'redirect_uri': 'https://quest.somnia.network/discord',
            'scope': 'identify',
            'state': 'eyJ0eXBlIjoiQ09OTkVDVF9ESVNDT1JEIn0=',
            'integration_type': '0'
        }

        oauth_url = 'https://discord.com/oauth2/authorize'
        oauth_referer = f'{oauth_url}?response_type=code&client_id=1318915934878040064&redirect_uri=https%3A%2F%2Fquest.somnia.network%2Fdiscord&scope=identify&state=eyJ0eXBlIjoiQ09OTkVDVF9ESVNDT1JEIn0='
        
        headers = self.auth_headers.copy()
        headers['referer'] = oauth_referer
        
        response = await self.send_request(
            request_type="GET",
            url='https://discord.com/api/v9/oauth2/authorize',
            params=params,
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get initial response: {response.text}")

        headers = self.auth_headers.copy()
        headers.update({
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'referer': oauth_referer
        })

        json_data = {
            "guild_id": "1284288403638325318",
            "permissions": "0",
            "authorize": True,
            "integration_type": 0,
            "location_context": {
                "guild_id": "10000",
                "channel_id": "10000",
                "channel_type": 10000
            }
        }

        auth_response = await self.send_request(
            request_type="POST",
            url='https://discord.com/api/v9/oauth2/authorize',
            params=params,
            headers=headers,
            json_data=json_data
        )

        if auth_response.status_code == 200:
            response_data = auth_response.json()
            if 'location' in response_data:
                parsed_url = urlparse(response_data['location'])
                query_params = parse_qs(parsed_url.query)
                if 'code' in query_params:
                    return query_params['code'][0]

        raise Exception(f"Failed to get authorization code: {auth_response.text}")