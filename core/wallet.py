from typing import Any

from better_proxy import Proxy
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_typing import ChecksumAddress
from eth_typing import HexStr

from pydantic import HttpUrl
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.contract import AsyncContract
from web3.eth import AsyncEth
from web3.types import Nonce, TxParams

from models import Erc20Contract

Account.enable_unaudited_hdwallet_features()


class Wallet(AsyncWeb3, Account):
    def __init__(self, mnemonic: str, rpc_url: HttpUrl | str, proxy: Proxy = None):
        provider = AsyncHTTPProvider(
            str(rpc_url),
            request_kwargs={
                "proxy": proxy.as_url if proxy else None,
                "ssl": False
            }
        )

        super().__init__(provider, modules={"eth": (AsyncEth,)})
        self.keypair = self.from_mnemonic(mnemonic) if len(mnemonic.split()) in (12, 24) else self.from_key(mnemonic)

    @property
    def wallet_address(self):
        return self.keypair.address

    @staticmethod
    def _get_checksum_address(address: str) -> ChecksumAddress:
        return AsyncWeb3.to_checksum_address(address)

    def get_contract(self, contract: Erc20Contract | str | object) -> AsyncContract:
        if isinstance(contract, str):
            return self.eth.contract(
                address=AsyncWeb3.to_checksum_address(contract),
                abi=Erc20Contract().abi
            )
        elif hasattr(contract, "address") and hasattr(contract, "abi"):
            return self.eth.contract(
                address=AsyncWeb3.to_checksum_address(contract.address),
                abi=contract.abi
            )
        else:
            raise TypeError(
                "Invalid contract type: expected Erc20Contract, str, or a contract-like object with address and abi")

    async def token_balance(self, token_address: str) -> int:
        contract = self.get_contract(token_address)

        return await contract.functions.balanceOf(
            AsyncWeb3.to_checksum_address(self.keypair.address)
        ).call()

    async def convert_amount_to_decimals(self, amount: float, token_address: str) -> int:
        if token_address == AsyncWeb3.to_checksum_address("0x0000000000000000000000000000000000000000") or token_address == AsyncWeb3.to_checksum_address("0x4200000000000000000000000000000000000006"):
            return AsyncWeb3.to_wei(amount, 'ether')

        token_contract = self.get_contract(token_address)
        decimals = await token_contract.functions.decimals().call()

        return int(amount * (10 ** decimals))
    
    async def convert_amount_from_decimals(self, amount: int, token_address: str) -> float:
        if token_address == AsyncWeb3.to_checksum_address("0x0000000000000000000000000000000000000000") or token_address == AsyncWeb3.to_checksum_address("0x4200000000000000000000000000000000000006"):
            return AsyncWeb3.from_wei(amount, 'ether')

        token_contract = self.get_contract(token_address)
        decimals = await token_contract.functions.decimals().call()

        return amount / (10 ** decimals)

    async def transactions_count(self) -> Nonce:
        return await self.eth.get_transaction_count(self.keypair.address)

    async def check_balance(self) -> None:
        balance = await self.eth.get_balance(self.keypair.address)

        if balance <= 0:
            raise Exception(f"ETH balance is empty")

    async def human_balance(self) -> float:
        balance = await self.eth.get_balance(self.keypair.address)
        return float(AsyncWeb3.from_wei(balance, "ether"))

    async def _build_base_transaction(self, contract_function) -> TxParams:
        gas_estimate = await contract_function.estimate_gas({"from": self.keypair.address})

        return {
            "gasPrice": await self.eth.gas_price,
            "nonce": await self.transactions_count(),
            "gas": int(gas_estimate * 1.2),
        }

    async def check_trx_availability(self, transaction: TxParams) -> None:
        balance = await self.human_balance()
        required = float(self.from_wei(int(transaction.get('value', 0)), "ether"))

        if balance < required:
            raise Exception(f"ETH balance is not enough. Required: {required} ETH | Available: {balance} ETH")

    async def _process_transaction(self, transaction: Any) -> tuple[bool, str]:
        try:
            status, result = await self.send_and_verify_transaction(transaction)
            return status, result

        except Exception as error:
            return False, str(error)

    async def get_signature(self, text: str, private_key: str | None = None) -> HexStr:
        encoded_message = encode_defunct(text=text)
        
        if private_key is not None:
            temp_keypair = self.from_key(private_key)
            signature = temp_keypair.sign_message(encoded_message)
        else:
            signature = self.keypair.sign_message(encoded_message)
            
        return HexStr(signature.signature.hex())

    async def send_and_verify_transaction(self, trx: Any) -> tuple[bool | Any, str]:
        signed = self.keypair.sign_transaction(trx)
        tx_hash = await self.eth.send_raw_transaction(signed.rawTransaction)
        receipt = await self.eth.wait_for_transaction_receipt(tx_hash)
        return receipt["status"] == 1, tx_hash.hex()

    async def _check_and_approve_token(
        self, token_address: str, spender_address: str, amount: int
    ) -> tuple[bool, str]:
        try:
            token_contract = self.get_contract(token_address)

            current_allowance = await token_contract.functions.allowance(
                self.wallet_address, spender_address
            ).call()

            if current_allowance >= amount:
                return True, "Allowance already sufficient"

            approve_tx = await token_contract.functions.approve(
                spender_address, amount
            ).build_transaction({
                "nonce": await self.transactions_count(),
                "gasPrice": int(await self.eth.gas_price * 1.25),
                "gas": 3_000_000,
                "from": self.wallet_address,
            })

            success, result = await self._process_transaction(approve_tx)
            if not success:
                return False, f"Approval failed: {result}"

            return True, "Approval successful"

        except Exception as error:
            return False, f"Error during approval: {str(error)}"