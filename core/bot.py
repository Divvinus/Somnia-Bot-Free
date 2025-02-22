import asyncio
import random

from core.modules import *
from loader import config
from models import Account
from loguru import logger
from utils import show_trx_log

class SomniaBot:
    @staticmethod
    async def process_account_statistics(account: Account) -> tuple[bool, str]:
        module = ProfileModule(account, config.referral_code)
        result = await module.get_account_statistics()
        if result:
            return True, "Account statistics completed successfully"
        return False, "Account statistics failed"
    
    @staticmethod
    async def process_profile(account: Account) -> tuple[bool, str]:
        module = ProfileModule(account, config.referral_code)
        result = await module.run()
        if result:
            return True, "Profile completed successfully"
        return False, "Profile failed"
    
    @staticmethod
    async def process_faucet(account: Account) -> tuple[bool, str]:
        module = FaucetModule(account)
        result = await module.faucet()
        if result:
            return True, "Faucet completed successfully"
        return False, "Faucet failed"
    
    @staticmethod
    async def process_transfer_stt(account: Account) -> tuple[bool, str]:
        module = TransferSTTModule(account, config.somnia_rpc)
        result = await module.transfer_stt()
        show_trx_log(module.wallet_address, f"Transfer STT", result[0], result[1])
        if result:
            return True, "Transfer STT completed successfully"
        return False, "Transfer STT failed"
    
    @staticmethod
    async def process_socials_quests_1(account: Account) -> tuple[bool, str]:
        module = SocialsQuest1Module(account)
        result = await module.run()
        if result:
            return True, "Socials quests 1 completed successfully"
        return False, "Socials quests 1 failed"