from Jam_Twitter_API.account_sync import TwitterAccountSync
from Jam_Twitter_API.errors import *

from core.wallet import Wallet
from models import Account
from loguru import logger


class TwitterWorker(Wallet):
    def __init__(self, account: Account):
        Wallet.__init__(self, account.pk_or_mnemonic, account.proxy)
        self.account = account
        self.twitter_client = None

    async def get_account(self):
        try:
            self.twitter_client = TwitterAccountSync.run(
                auth_token=self.account.auth_token,
                proxy=str(self.account.proxy),
                setup_session=True
            )
            return self.twitter_client

        except TwitterAccountSuspended as error:
            logger.error(f"Account: {self.wallet_address} | Account is suspended: {error}")
            return None

        except TwitterError as error:
            logger.error(
                f"Account: {self.wallet_address} | Twitter error occurred: {error.error_message} | {error.error_code}")
            return None

        except IncorrectData as error:
            logger.error(f"Account: {self.wallet_address} | Incorrect data provided: {error}")
            return None

        except RateLimitError as error:
            logger.error(f"Account: {self.wallet_address} | Rate limit exceeded: {error}")
            return None