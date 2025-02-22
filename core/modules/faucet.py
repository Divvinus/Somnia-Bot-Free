from loguru import logger

from models import Account
from core.wallet import Wallet
from core.api import BaseAPIClient


class FaucetModule(Wallet, BaseAPIClient):
    def __init__(self, account: Account):
        Wallet.__init__(self, account.pk_or_mnemonic, account.proxy)
        BaseAPIClient.__init__(self, base_url="https://testnet.somnia.network", proxy=account.proxy)  
        
    async def faucet(self):
        logger.info(f"Account {self.wallet_address} | Processing faucet...")
        
        headers = {
            'authority': 'testnet.somnia.network',
            'accept': '*/*',
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://testnet.somnia.network',
            'referer': 'https://testnet.somnia.network/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }
        
        json_data = {
            'address': self.wallet_address,
        }
        
        response = await self.send_request(request_type="POST", method="/api/faucet", json_data=json_data, headers=headers, verify=False)
        response = response.json()
        
        if response.get("error"):
            if response.get("error") == "Please wait 24 hours between requests":
                logger.warning(f"Account {self.wallet_address} | Tokens have already been received for this wallet today, come back tomorrow")
                return True
            else:
                logger.error(f"Account {self.wallet_address} | {response.get('error')}")
                return False
        else:
            logger.success(f"Account {self.wallet_address} | Successfully requested test tokens")
            return True