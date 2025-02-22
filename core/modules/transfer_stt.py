import random
import asyncio

from loguru import logger

from models import Account
from core.wallet import Wallet
from core.api import BaseAPIClient


class TransferSTTModule(Wallet, BaseAPIClient):
    def __init__(self, account: Account):
        Wallet.__init__(self, account.pk_or_mnemonic, account.proxy)
        BaseAPIClient.__init__(self, base_url="https://quest.somnia.network/api", proxy=account.proxy)  
        
    async def random_sleep(self, min_sec=30, max_sec=60):
        delay = random.uniform(min_sec, max_sec)
        logger.info(f"Account {self.wallet_address} | Sleep {delay} seconds...")
        await asyncio.sleep(delay)
        
    async def transfer_stt(self):
        pass
    
    async def submit_transfer_tx(self):
        pass
    
    async def run(self):
        await self.transfer_stt()
        
        await self.random_sleep()
        
        await self.submit_transfer_tx()

