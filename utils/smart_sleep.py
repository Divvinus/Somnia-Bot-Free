import asyncio
import random

from loguru import logger


async def random_sleep(account_name: str = "Referral", min_sec: int = 30, max_sec: int = 60) -> None:
    delay = random.uniform(min_sec, max_sec)
    minutes = int(delay // 60)
    seconds = round(delay % 60, 1)

    if minutes > 0:
        logger.info(f"Account {account_name} | Sleep {minutes}m {seconds}s")
    else:
        logger.info(f"Account {account_name} | Sleep {seconds}s")

    await asyncio.sleep(delay)