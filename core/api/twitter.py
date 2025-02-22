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
        
    async def connect_twitter(self):
        try:
            twitter_client = await self.get_account()
            if not twitter_client:
                logger.error(f"Account: {self.wallet_address} | Failed to get Twitter account | auth_token: {self.account.auth_token}")
                return

            ct0_token = twitter_client.ct0

            bind_params = {
                "code_challenge": "challenge123",
                "code_challenge_method": "plain",
                "client_id": "WS1FeDNoZnlqTEw1WFpvX1laWkc6MTpjaQ",
                "redirect_uri": "https://quest.somnia.network/twitter",
                "response_type": "code",
                "scope": "users.read follows.write tweet.write like.write tweet.read",
                "state": "eyJ0eXBlIjoiQ09OTkVDVF9UV0lUVEVSIn0="
            }
            
            session = twitter_client.session
            response = session.get(
                "https://twitter.com/i/api/2/oauth2/authorize", 
                params=bind_params, 
                headers={
                    'authority': 'twitter.com',
                    'accept': '*/*',
                    'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
                    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                    'cookie': f'auth_token={self.account.auth_token}; ct0={ct0_token}',
                    'x-csrf-token': ct0_token,
                }
            )

            response_data = response.json()
            auth_code = response_data['auth_code']

            approve_params = {
                "approval": "true",
                "code": auth_code
            }

            response = session.post(
                "https://twitter.com/i/api/2/oauth2/authorize", 
                params=approve_params, 
                headers={
                    'authority': 'twitter.com',
                    'accept': '*/*',
                    'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
                    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                    'cookie': f'auth_token={self.account.auth_token}; ct0={ct0_token}',
                    'x-csrf-token': ct0_token,
                }
            )
            
            redirect_uri = response.json()['redirect_uri']
            code = redirect_uri.split('code=')[1].split('&')[0]
            
            print(code)

            return code
        
        except Exception as e:
            logger.error(f"Account: {self.wallet_address} | Error while connecting Twitter: {e}")