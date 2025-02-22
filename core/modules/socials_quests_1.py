import json
import secrets

from eth_keys import keys
from eth_utils import to_checksum_address

from loguru import logger
from models import Account
from core.api import SomniaWorker


class SocialsQuest1Module(SomniaWorker):
    def __init__(self, account: Account):
        super().__init__(account)

    @staticmethod
    def get_incomplete_quests(response: dict) -> list:
        quests = response.get("quests", [])
        incomplete_quests = [
            quest["type"] for quest in quests if not quest.get("isParticipated", False)
        ]
        return incomplete_quests

    @staticmethod
    def generate_eth_address() -> tuple:
        private_key_bytes = secrets.token_bytes(32)
        private_key = keys.PrivateKey(private_key_bytes)
        public_key = private_key.public_key
        address = to_checksum_address(public_key.to_address())
        return private_key, address

    async def get_quests(self) -> dict:
        self.base_headers = {
            "authority": "quest.somnia.network",
            "accept": "*/*",
            "authorization": self.base_headers["authorization"],
            "origin": "https://quest.somnia.network",
            "referer": "https://quest.somnia.network/campaigns/2",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        return await self.send_request(
            request_type="GET", 
            method="/campaigns/2", 
            headers=self.base_headers
        )

    async def onboarding_referral(self, private_key: str, address: str) -> str:
        logger.info("Referral Account | Onboarding...")

        signature = await self.get_signature(
            '{"onboardingUrl":"https://quest.somnia.network"}',
            private_key=private_key,
        )

        headers = {
            "authority": "quest.somnia.network",
            "accept": "application/json",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://quest.somnia.network",
            "referer": "https://quest.somnia.network/connect?redirect=%2F",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

        json_data = {
            "signature": signature,
            "walletAddress": address,
        }

        response = await self.send_request(
            request_type="POST",
            method="/auth/onboard",
            json_data=json_data,
            headers=headers,
        )
        response = response.json()
        return response["token"]

    async def register_referral(self, token: str, referral_code: str, private_key: str) -> bool:
        self.base_url = "https://quest.somnia.network/api"

        try:
            message_to_sign = json.dumps(
                {"referralCode": referral_code, "product": "QUEST_PLATFORM"},
                separators=(",", ":"),
            )
            signature = await self.get_signature(message_to_sign, private_key=private_key)

            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": "https://quest.somnia.network",
                "priority": "u=1, i",
                "referer": f"https://quest.somnia.network/referrals/{referral_code}",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            }

            json_data = {
                "referralCode": referral_code,
                "product": "QUEST_PLATFORM",
                "signature": signature,
            }

            response = await self.send_request(
                request_type="POST",
                method="/users/referrals",
                json_data=json_data,
                headers=headers,
            )
            response = response.json()

            if not response:
                logger.info(f"Successfully registered referral for code {referral_code}")
                return True

            try:
                response_data = json.loads(response) if isinstance(response, str) else response
                if response_data.get("message") == "Success":
                    logger.info(f"Successfully registered referral for code {referral_code}")
                    return True
                else:
                    logger.error(f"Failed to register referral for code {referral_code}. Response: {response_data}")
                    return False
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Failed to parse response: {response}. Error: {e}")
                return False

        except Exception as e:
            logger.error(f"Error processing referral for code {referral_code}: {str(e)}")
            return False

    async def connect_discord(self) -> bool:
        json_data = {"questId": 12}

        response = await self.send_request(
            request_type="POST",
            method="/social/discord/connect",
            headers=self.base_headers,
            json_data=json_data,
        )
        response = response.json()
        
        if response.get("success") is True:
            logger.success(f"Account {self.wallet_address} | Discord connected successfully")
            return True
        else:
            logger.error(f"Account {self.wallet_address} | Failed to connect Discord. Response: {response}")
            return False

    async def connect_twitter(self) -> bool:
        json_data = {"questId": 3}

        response = await self.send_request(
            request_type="POST",
            method="/social/twitter/connect",
            headers=self.base_headers,
            json_data=json_data,
        )
        response = response.json()
        if response.get("success") is True:
            logger.success(f"Account {self.wallet_address} | Twitter connected successfully")
            return True
        else:
            logger.error(f"Account {self.wallet_address} | Failed to connect Twitter")
            return False

    async def referral(self) -> bool:
        try:
            while True:
                referral_code = await self.get_me_info(get_referral_code=True)
                if referral_code is None:
                    await self.activate_referral()
                else: break
            private_key, address = self.generate_eth_address()
            token = await self.onboarding_referral(private_key, address)            
            return await self.register_referral(token, referral_code, private_key)
        except Exception as e:
            logger.error(f"Account {self.wallet_address} | Error in referral method: {e}")
            return False

    async def run(self) -> bool:
        try:
            logger.info(f"Account {self.wallet_address} | Starting the socials quests module...")

            if not await self.onboarding():
                logger.error(f"Account {self.wallet_address} | Failed to authorize on Somnia")
                return False

            for _ in range(3):
                logger.info(f"Account {self.wallet_address} | Getting quests...")
                response = await self.get_quests()
                response_data = response if isinstance(response, dict) else response.json()
                incomplete_quests = self.get_incomplete_quests(response_data)

                if "CONNECT_DISCORD" in incomplete_quests:
                    await self.connect_discord()
                if "CONNECT_TWITTER" in incomplete_quests:
                    await self.connect_twitter()
                if "REFERRAL" in incomplete_quests:
                    await self.referral()
                else:
                    logger.success(f"Account {self.wallet_address} | All quests are completed")
                    return True
        except Exception as e:
            logger.error(f"Account {self.wallet_address} | Error in run method: {e}")
            return False