import asyncio

import aiohttp
from bip_utils.bip import bip39
from eth_account import Account
from eth_account.account import LocalAccount
from eth_account.messages import encode_defunct
from loguru import logger
from web3.auto import w3

from utils import loader, append_file


class Checker:
    def __init__(self,
                 account_data: str) -> None:
        if bip39.Bip39MnemonicValidator().IsValid(mnemonic=account_data):
            self.account: LocalAccount = Account.from_mnemonic(mnemonic=account_data)

        else:
            self.account: LocalAccount = Account.from_key(private_key=account_data)

    async def get_proofs(self,
                         client: aiohttp.ClientSession) -> dict[str, str]:
        while True:
            response_text: None = None

            try:
                message_hash = w3.keccak(text=f'Claiming Aevo Airdrop {self.account.address}')
                signature = self.account.sign_message(encode_defunct(message_hash)).signature.hex()
                r: aiohttp.ClientResponse = await client.get(
                    url='https://api-ribbon.vercel.app/api/aevo/airdrop-proof',
                    params={
                        'address': self.account.address,
                        'message': f'Claiming Aevo Airdrop {self.account.address}',
                        'signature': signature
                    }
                )

                response_text: str = await r.text()
                response_json: dict = await r.json(content_type=None)

                return response_json['data']['claim']

            except Exception as error:
                if response_text:
                    logger.error(f'{self.account.address} | Unexpected Error When Getting Proof: {error}, '
                                 f'repsponse: {response_text}')

                else:
                    logger.error(f'{self.account.address} | Unexpected Error When Getting Proof: {error}')

    async def start_checker(self,
                            client: aiohttp.ClientSession) -> None:
        proof_result: dict[str, str] = await self.get_proofs(client=client)
        amount: int = int(proof_result['amount'], 16)

        if amount > 0:
            logger.success(f'{self.account.address} | {amount}')

            async with asyncio.Lock():
                await append_file(file_path='result/with_tokens.txt',
                                  file_content=f'{self.account.key.hex()}\n')

            return

        logger.error(f'{self.account.address} | {amount}')


async def start_checker(account_data: str,
                        client: aiohttp.ClientSession) -> None:
    async with loader.semaphore:
        try:
            await Checker(
                account_data=account_data
            ).start_checker(
                client=client
            )

        except Exception as error:
            logger.error(f'{account_data} | Unexpected Error: {error}')

            await append_file(file_path=f'result/errors.txt',
                              file_content=f'{account_data}\n')
