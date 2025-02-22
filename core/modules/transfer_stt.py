import random
import asyncio
import secrets

from eth_keys import keys
from eth_utils import to_checksum_address

from loguru import logger
from models import Account
from core.wallet import Wallet


class TransferSTTModule(Wallet):
    def __init__(self, account: Account, rpc_url: str):
        Wallet.__init__(self, account.pk_or_mnemonic, rpc_url, account.proxy)
        
    @staticmethod
    def generate_eth_address():
        private_key_bytes = secrets.token_bytes(32)
        private_key = keys.PrivateKey(private_key_bytes)
        public_key = private_key.public_key
        address = to_checksum_address(public_key.to_address())
        return address
        
    async def transfer_stt(self):
        logger.info(f"Account {self.wallet_address} | Processing transfer_stt...")
        try:
            recipient_address = self.generate_eth_address()
            
            balance = await self.human_balance()
            
            if balance > 0.01: amount = 0.01
            elif balance > 0.005: amount = 0.005
            elif balance > 0.001: amount = 0.001
            else:
                logger.error(f"Account {self.wallet_address} | Not enough balance")
                return False, "Not enough balance"
                                  
            transaction = {
                "from": self.wallet_address,
                "to": recipient_address,
                "value": self.to_wei(amount, "ether"),
                "nonce": await self.transactions_count(),
                "gasPrice": await self.eth.gas_price,
                "gas": 21000
            }
            
            await self.check_trx_availability(transaction)
            
            status, tx_hash = await self._process_transaction(transaction)
            
            if status: return True, tx_hash
            else: return False, tx_hash
                
        except Exception as e:
            logger.error(f"Account {self.wallet_address} | Error in transfer_stt: {str(e)}")
            return False, str(e)
            