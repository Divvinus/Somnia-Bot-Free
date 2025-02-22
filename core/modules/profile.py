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

    async def connect_discord_account(self) -> bool:
        logger.info(f"Account {self.wallet_address} | Trying to link a Discord account to a website...")
        code = await self.discord_worker._request_authorization()

        url = "https://quest.somnia.network/api/auth/socials"
        headers = {
            "authority": "quest.somnia.network",
            "accept": "*/*",
            "accept-language": "ru,en-US;q=0.9,en;q=0.8",
            "authorization": f"Bearer {self.authorization_token}",
            "content-type": "application/json",
            "origin": "https://quest.somnia.network",
            "referer": f"https://quest.somnia.network/discord?code={code}&state=eyJ0eXBlIjoiQ09OTkVDVF9ESVNDT1JEIn0%3D",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

        response = await self.send_request(
            request_type="POST",
            url=url,
            headers=headers,
            json_data={"code": code, "provider": "discord"},
            verify=False,
        )

        if response.status_code == 200:
            try:
                response_data: dict = response.json()
                if response_data.get("success"):
                    logger.success(f"Account {self.wallet_address} | Discord account connected successfully")
                    return True
            except Exception as e:
                logger.error(f"Account {self.wallet_address} | Error: {e}")
                return False
        else:
            logger.error(f"Account {self.wallet_address} | Failed to connect Discord account")
            logger.error(f"Account {self.wallet_address} | Error: {response}")
            return False

    async def connect_twitter_account(self) -> bool:
        logger.info(f"Account {self.wallet_address} | Trying to connect Twitter account...")
        code = await self.twitter_worker.connect_twitter()
        if not code:
            return False

        headers = {
            "authority": "quest.somnia.network",
            "accept": "*/*",
            "authorization": f"Bearer {self.authorization_token}",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://quest.somnia.network",
            "referer": f"https://quest.somnia.network/twitter?state=eyJ0eXBlIjoiQ09OTkVDVF9UV0lUVEVSIn0%3D&code={code}",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

        json_data = {
            "code": code,
            "codeChallenge": "challenge123",
            "provider": "twitter",
        }

        response = await self.send_request(
            request_type="POST",
            method="/auth/socials",
            json_data=json_data,
            headers=headers,
        )

        if response.status_code == 200:
            try:
                response_data: dict = response.json()
                if response_data.get("success"):
                    logger.success(f"Account {self.wallet_address} | Twitter account connected successfully")
                    return True
            except Exception as e:
                logger.error(f"Account {self.wallet_address} | Error: {e}")
                return False
        else:
            logger.error(f"Account {self.wallet_address} | Failed to connect Twitter account")
            logger.error(f"Account {self.wallet_address} | Error: {response}")
            return False

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
        logger.info(f"Account {self.wallet_address} | Getting account statistics...")
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
            
            referral_code = await self.get_me_info(get_referral_code=True)
            if referral_code is None:
                await self.activate_referral()

            null_fields = await self.get_me_info()
            logger.info(f"Account {self.wallet_address} | Getting the user info...")
            await random_sleep(self.wallet_address, 30, 60)

            if any(value is None for value in null_fields.values()):
                if null_fields.get("username") is None:
                    if not await self.create_username():
                        return False
                    await random_sleep(self.wallet_address, 60, 120)

                if null_fields.get("discordName") is None and self.account.token_discord:
                    if not await self.connect_discord_account():
                        return False
                    await random_sleep(self.wallet_address, 120, 240)

                if null_fields.get("twitterName") is None and self.account.auth_token:
                    if not await self.connect_twitter_account():
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