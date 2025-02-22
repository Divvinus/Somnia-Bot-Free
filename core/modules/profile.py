import asyncio
import json

from loguru import logger
from models import Account
from core.api import SomniaWorker, TwitterWorker, DiscordConnectModule
from utils import generate_username, random_sleep


class ProfileModule(SomniaWorker):
    def __init__(self, account: Account, referral_code: str):
        super().__init__(account)
        self.twitter_worker = TwitterWorker(account)
        self.discord_worker = DiscordConnectModule(account)
        self.referral_code = referral_code

    async def create_username(self) -> bool:
        logger.info(f"Account {self.wallet_address} | Trying to set the username...")
        while True:
            username = generate_username()
            json_data = {"username": username}
            headers = {
                "authority": "quest.somnia.network",
                "accept": "application/json",
                "authorization": self.base_headers["authorization"],
                "content-type": "application/json",
                "origin": "https://quest.somnia.network",
                "referer": "https://quest.somnia.network/account",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            }

            try:
                response = await self.send_request(
                    request_type="PATCH",
                    method="/users/username",
                    json_data=json_data,
                    headers=headers,
                    verify=False,
                )

                if response.status_code in [200, 201, 204]:
                    logger.info(f"Account {self.wallet_address} | Created username {username}")
                    return True

                logger.error(
                    f"Account {self.wallet_address} | Failed to create username {username}. Status: {response.status_code}"
                )
                await asyncio.sleep(2)

            except Exception as error:
                logger.error(f"Account {self.wallet_address} | Error: {error}")
                await asyncio.sleep(2)

    async def referral_bind(self) -> None:
        if not self.referral_code:
            logger.error(f"Account {self.wallet_address} | Referral code not found")
            return

        message_to_sign = json.dumps(
            {"referralCode": self.referral_code, "product": "QUEST_PLATFORM"},
            separators=(",", ":"),
        )
        signature = await self.get_signature(message_to_sign)

        headers = {
            "accept": "application/json",
            "authorization": self.base_headers["authorization"],
            "content-type": "application/json",
            "origin": "https://quest.somnia.network",
            "priority": "u=1, i",
            "referer": f"https://quest.somnia.network/referrals/{self.referral_code}",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

        json_data = {
            "referralCode": self.referral_code,
            "product": "QUEST_PLATFORM",
            "signature": signature,
        }

        await self.send_request(
            request_type="POST",
            method="/users/referrals",
            json_data=json_data,
            headers=headers,
            verify=False,
        )
        
    async def get_account_statistics(self):
        if not await self.onboarding():
            logger.error(f"Account {self.wallet_address} | Failed to authorize on Somnia")
            return False
        await self.get_stats()

    async def run(self) -> bool:
        try:
            logger.info(f"Account {self.wallet_address} | Starting the profile module...")
            
            if not await self.onboarding():
                logger.error(f"Account {self.wallet_address} | Failed to authorize on Somnia")
                return False
                
            logger.info(f"Account {self.wallet_address} | Authorized on the site Somnia")
            await random_sleep(self.wallet_address, 30, 60)

            await self.referral_bind()
            logger.info(f"Account {self.wallet_address} | Referral code bound to the account")
            await random_sleep(self.wallet_address, 60, 120)

            null_fields = await self.get_me_info()
            logger.info(f"Account {self.wallet_address} | Getting the user info...")
            await random_sleep(self.wallet_address, 30, 60)

            if any(value is None for value in null_fields.values()):
                if null_fields.get("username") is None:
                    if not await self.create_username():
                        return False
            else:
                await self.get_stats()
                logger.success(
                    f"Account {self.wallet_address} | Name is set and all social networks are linked to the account"
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Account {self.wallet_address} | Error in run method: {e}")
            return False