import json

from loguru import logger

from models import Account
from core.wallet import Wallet
from core.api import BaseAPIClient


class FaucetModule(Wallet, BaseAPIClient):
    def __init__(self, account: Account):
        Wallet.__init__(self, account.pk_or_mnemonic, account.proxy)
        BaseAPIClient.__init__(self, base_url="https://quest.somnia.network/api", proxy=account.proxy)  
        
    async def faucet(self):
        headers = {
            'authority': 'devnet.somnia.network',
            'accept': '*/*',
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://devnet.somnia.network',
            'referer': 'https://devnet.somnia.network/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }
        
        json_data = {
            'address': self.wallet_address,
        }
        
        response: dict = await self.send_request(request_type="POST", method="/faucet", json_data=json_data, headers=headers, verify=False)
        response = json.loads(response)
        if response.get("error"):
            if response.get("error") == "Rate limit exceeded. Maximum 1 request per IP per 24 hours.":
                logger.warning(f"Account {self.wallet_address} | Tokens have already been received for this wallet today, come back tomorrow")
            else:
                logger.error(f"Account {self.wallet_address} | {response.get('error')}")
        else:
            logger.info(f"Account {self.wallet_address} | Faucet success")