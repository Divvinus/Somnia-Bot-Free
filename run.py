import asyncio
import random
import sys
import os
from typing import Callable, Dict

from loguru import logger
from core.bot import SomniaBot  
from loader import config, semaphore, progress
from models import Account
from utils import setup
from console import Console


def get_address(mnemonic):
    from eth_account import Account
    account = Account()
    keypair = account.from_mnemonic(mnemonic) if len(mnemonic.split()) in (12, 24) else account.from_key(mnemonic)
    return keypair.address

async def process_execution(account: Account, process_func):
    address = get_address(account.pk_or_mnemonic)
    async with semaphore:
        try:
            min_delay = config.delay_before_start.min
            max_delay = config.delay_before_start.max

            if isinstance(min_delay, (int, float)) and isinstance(max_delay, (int, float)):
                if 0 < min_delay <= max_delay and max_delay > 0:
                    delay = random.uniform(min_delay, max_delay)
                    logger.info(f"🔄 Account: {address} | Applying initial delay of {delay:.2f} seconds")
                    await asyncio.sleep(delay)

            status, result = await process_func(account)
            if status:
                progress.increment()
                logger.info(f"🔄 Accounts processed: {progress.processed}/{progress.total}")

        except Exception as e:
            logger.error(f"❌ Account: {address} | Error during execution: {str(e)}")

async def main_loop() -> None:
    while True:
        console = Console()
        console.build()

        if config.module == "exit":
            sys.exit(0)
        else:
            module_functions: Dict[str, Callable] = {
                name: getattr(SomniaBot, f"process_{name}")
                for name in Console.MODULES_DATA.values()
                if name != "exit"
            }

            process_func = module_functions.get(config.module)
            if process_func:
                try:
                    if config.module == "recruiting_referrals":
                        account = config.accounts[0]
                        await process_execution(account, process_func)
                        logger.info(f"🔄 Accounts processed: 1/1")
                    else:
                        tasks = [
                            asyncio.create_task(process_execution(account, process_func))
                            for account in config.accounts
                        ]
                        await asyncio.gather(*tasks)
                except Exception as e:
                    address = get_address(config.accounts[0].pk_or_mnemonic)
                    logger.error(f"❌ Account: {address} | Error during execution: {str(e)}")
            else:
                address = get_address(config.accounts[0].pk_or_mnemonic)
                logger.warning(f"❌ Account: {address} | Module {config.module} not implemented yet!")

            progress.processed = 0
            
            input("\nPress Enter to continue...")
            os.system("cls" if os.name == "nt" else "clear")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    setup()
    asyncio.run(main_loop())