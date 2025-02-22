
from core.wallet import Wallet
from core.api import BaseAPIClient
from models import Account
from loguru import logger
from utils import random_sleep

class SomniaWorker:
    def __init__(self, account: Account):
        self.account = account
        self.wallet = Wallet(account.pk_or_mnemonic, account.proxy)
        self.api = BaseAPIClient(base_url="https://quest.somnia.network/api", proxy=account.proxy)
        self.authorization_token = None
        self.base_headers = None

    @property
    def wallet_address(self):
        return self.wallet.wallet_address

    async def get_signature(self, *args, **kwargs):
        return await self.wallet.get_signature(*args, **kwargs)

    async def send_request(self, *args, **kwargs):
        return await self.api.send_request(*args, **kwargs)
        
    async def onboarding(self) -> bool:
        try:
            signature = await self.get_signature('{"onboardingUrl":"https://quest.somnia.network"}')
            
            headers = {
                'authority': 'quest.somnia.network',
                'accept': 'application/json',
                'content-type': 'application/json',
                'dnt': '1',
                'origin': 'https://quest.somnia.network',
                'referer': 'https://quest.somnia.network/connect?redirect=%2F',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin'
            }
            
            json_data = {
                'signature': signature,
                'walletAddress': self.wallet_address,
            }
            
            response = await self.send_request(
                request_type="POST", 
                method="/auth/onboard", 
                json_data=json_data, 
                headers=headers
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Account {self.wallet_address} | Onboarding failed with status code: {response.status_code}")
                return False
                
            response_data = response.json()
            
            if not response_data.get("token"):
                logger.error(f"Account {self.wallet_address} | No token in onboarding response")
                return False
                
            self.authorization_token = response_data["token"]
            self.base_headers = {
                'authority': 'quest.somnia.network',
                'accept': 'application/json',
                'authorization': f'Bearer {self.authorization_token}',
                'content-type': 'application/json',
                'dnt': '1',
                'referer': 'https://quest.somnia.network/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin'
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Account {self.wallet_address} | Onboarding error: {e}")
            return False

    async def get_stats(self):
        response = await self.send_request(request_type="GET", method="/stats", headers=self.base_headers)
        response = response.json()
        
        logger.info(
            f"Account: {self.wallet_address}\n"
            f"{'='*50}\n"
            f"🏆 Total Points: {response.get('totalPoints', '0')}\n"
            f"🚀 Total Boosters: {response.get('totalBoosters', '0')}\n"
            f"🎯 Final Points: {response.get('finalPoints', '0')}\n"
            f"📊 Rank: {response.get('rank', 'N/A')}\n"
            f"🔄 Season ID: {response.get('seasonId', 'N/A')}\n"
            f"👥 Total Referrals: {response.get('totalReferrals', '0')}\n"
            f"✅ Quests Completed: {response.get('questsCompleted', '0')}\n"
            f"⚡ Daily Booster: {response.get('dailyBooster', '0')}\n"
            f"🔥 Streak Count: {response.get('streakCount', '0')}\n"
            f"{'='*50}"
        )

    async def get_me_info(self, get_referral_code: bool = False):
        response = await self.send_request(request_type="GET", method="/users/me", headers=self.base_headers)
        response = response.json()
        
        if get_referral_code:
            return response.get("referralCode")

        null_fields = {
            key: value for key, value in response.items() 
            if value is None and key in [
                'username', 
                'discordName', 
                'twitterName'
            ]
        }
   
        return null_fields
    
    async def activate_referral(self):
        logger.info(f"Account {self.wallet_address} | Activating your account")
        success = False
        
        for _ in range(3):
            response = await self.send_request(
                request_type="POST", 
                method="/referrals", 
                headers=self.base_headers,
                verify=False
            ) 
            if response.status_code == 200:
                logger.success(f"Account {self.wallet_address} | Account activated")
                success = True
                break
            if response.status_code == 500:
                logger.warning(f"Account {self.wallet_address} | The server cannot process the request, try to activate the account again...")
                await random_sleep(self.wallet_address, 2, 5)
                continue
            else:
                logger.error(f"Account {self.wallet_address} | Account activation failed. Reason: {response.json()}")
                break
        
        if not success:
            logger.warning(f"Account {self.wallet_address} | Failed to activate account after 3 attempts. Please try again later")