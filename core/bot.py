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
    
    
# def get_address(mnemonic):
#     from eth_account import Account
#     account = Account()
#     keypair = account.from_mnemonic(mnemonic) if len(mnemonic.split()) in (12, 24) else account.from_key(mnemonic)
#     return keypair.address

# class SingularityAutoBot:
#     def __init__(self, account: Account):
#         self.account = account
#         self.wallet_address = get_address(account.pk_or_mnemonic)
#         self.tasks = [
#             self.process_zealy,
#             self.process_swap_sfi_aimm,
#             self.process_add_liquidity_sfi_aimm,
#             self.process_remove_liquidity_sfi_aimm,
#             self.process_staking_wsfi,
#             self.process_unstaking_wsfi,
#             self.process_staking_claim,
#         ]
#         self.completed_tasks = set()
#         self.task_attempt_count = {task.__name__: 0 for task in self.tasks}
#         self.MAX_ATTEMPTS_PER_TASK = 20
        
#     async def smart_sleep(self):
#         sleep = random.randint(100, 500)
#         logger.info(f"⌛️ Account: {self.wallet_address} | Waiting for {sleep} seconds")
#         await asyncio.sleep(sleep)

#     async def run(self) -> tuple[bool, str]:
#         await self.process_request_faucet()
#         await self.smart_sleep()
        
#         task_success_count = {task.__name__: 0 for task in self.tasks}
        
#         task_required_success = {
#             "process_staking_wsfi": 2,
#             "process_swap_sfi_aimm": 3,
#             "process_staking_claim": 2
#         }
        
#         random.shuffle(self.tasks)
        
#         while any(
#             task_success_count[task.__name__] < task_required_success.get(task.__name__, 1)
#             for task in self.tasks
#             if self.task_attempt_count[task.__name__] < self.MAX_ATTEMPTS_PER_TASK
#         ):
#             task = random.choice(self.tasks)
#             required = task_required_success.get(task.__name__, 1)
#             if task_success_count[task.__name__] < required and self.task_attempt_count[task.__name__] < self.MAX_ATTEMPTS_PER_TASK:
#                 self.task_attempt_count[task.__name__] += 1
#                 result, message = await task()
#                 if result:
#                     task_success_count[task.__name__] += 1
#                     logger.success(f"✅ Task {task.__name__} completed successfully ({task_success_count[task.__name__]}/{required})")
#                 else:
#                     attempts_left = self.MAX_ATTEMPTS_PER_TASK - self.task_attempt_count[task.__name__]
#                     logger.warning(f"⚠️  Task {task.__name__} failed: {message}. Attempts left: {attempts_left}")
                
#                 await self.smart_sleep()
                        
#         return True, "All tasks completed successfully"

#     async def get_token_balances(self) -> dict[str, float]:
#         module = SwapModule(self.account, config.sfi_rpc)
#         tokens = config.swap_config.tokens
#         balances = {}
#         for token in tokens:
#             if token.name == "SFI":
#                 balances[token.name] = await module.eth.get_balance(self.wallet_address)
#             else:
#                 balances[token.name] = await module.token_balance(token.address)
#         return balances

#     async def process_request_faucet(self) -> tuple[bool, str]:
#         return await SingularityBot.process_request_faucet(self.account)

#     async def process_zealy(self) -> tuple[bool, str]:
#         return await SingularityBot.process_zealy(self.account)

#     async def process_swap_sfi_aimm(self) -> tuple[bool, str]:
#         if not await self.ensure_token_balance("SFI", 1):
#             logger.error(f"❌ Account: {self.wallet_address} | Failed to ensure SFI balance")
#             return False, "❌ Not enough SFI tokens to perform swap"

#         if not await self.ensure_token_balance("AIMM", 1):
#             logger.error(f"❌ Account: {self.wallet_address} | Failed to ensure AIMM balance")
#             return False, "❌ Not enough AIMM tokens to perform swap"

#         result, message = await self._execute_swap("SFI", "AIMM")

#         return result, message

#     async def ensure_token_balance(self, token_name: str, min_balance: float) -> bool:
#         token_swap_options = {
#             "AIMM": ["SFI", "WSFI", "USDC"],
#             "SFI": ["USDC", "WSFI"],
#             "WSFI": ["SFI", "USDC", "AIMM"]
#         }

#         if token_name in token_swap_options:
#             for source_token in token_swap_options[token_name]:
#                 balances = await self.get_token_balances()
#                 if balances.get(source_token, 0) > min_balance:
#                     result, _ = await self._execute_swap(source_token, token_name)
#                     if result:
#                         await self.smart_sleep()
#                         return True
            
#             logger.warning(f"⚠️  Account: {self.wallet_address} | Failed to acquire {token_name} via any swap route")
#             return False

#     async def _execute_swap(self, input_token: str, output_token: str) -> tuple[bool, str]:
#         module = SwapModule(self.account, config.sfi_rpc)
#         tokens = config.swap_config.tokens

#         input_address = next(token.address for token in tokens if token.name == input_token)
#         output_address = next(token.address for token in tokens if token.name == output_token)

#         balance = await (
#             module.eth.get_balance(self.wallet_address) if input_token == "SFI" else module.token_balance(
#                 input_address))

#         if balance <= 0.01:
#             return False, f"❌ Not enough {input_token} to swap."

#         if config.swap_config.full_balance:
#             amount = balance * 0.95
#         elif config.swap_config.percentage_amount_flag:
#             amount = balance * (config.swap_config.percentage_amount / 100)
#         else:
#             return False, "❌ Incorrect token calculation configuration in config/settings.yaml"

#         amount = module.from_wei(int(amount), 'ether')

#         logger.info(
#             f"🔄 Account: {self.wallet_address} | Processing swap of {amount} {input_token} to {output_token}."
#         )
#         status, result = await module.process_swap(amount, input_token, input_address, output_token, output_address)
#         show_trx_log(self.wallet_address, f"Swap {amount} {input_token} to {output_token}", status, result)

#         return status, result

#     async def process_add_liquidity_sfi_aimm(self) -> tuple[bool, str]:
#         if not await self.ensure_token_balance("SFI", 1) or not await self.ensure_token_balance("AIMM", 1):
#             return False, "❌ Not enough SFI or AIMM tokens to add liquidity"

#         result, message = await SingularityBot.process_add_liquidity(self.account, [("SFI", "AIMM")])
#         return result, message

#     async def process_remove_liquidity_sfi_aimm(self) -> tuple[bool, str]:
#         result, message = await SingularityBot.process_remove_liquidity(self.account, [("SFI", "AIMM")])
#         return result, message

#     async def process_staking_wsfi(self) -> tuple[bool, str]:
#         if not await self.ensure_token_balance("WSFI", 1):
#             return False, "❌ Not enough WSFI tokens to stake"

#         result, message = await SingularityBot.process_staking(self.account, False)
#         return result, message

#     async def process_unstaking_wsfi(self) -> tuple[bool, str]:
#         result, message = await SingularityBot.process_unstaking(self.account, False)
#         return result, message

#     async def process_staking_claim(self) -> tuple[bool, str]:
#         result, message = await SingularityBot.process_staking_claim(self.account)
#         return result, message