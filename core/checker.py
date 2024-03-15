import asyncio

import aiohttp
from bip_utils.bip import bip39
from eth_account import Account
from eth_account.account import LocalAccount
from loguru import logger
from web3.auto import w3

from utils import loader, append_file

Account.enable_unaudited_hdwallet_features()


class AccountData:
    def __init__(self,
                 address: str,
                 private_key: str | None = None,
                 mnemonic: str | None = None):
        self.address: str = address
        self.private_key: str | None = private_key
        self.mnemonic: str | None = mnemonic


class Checker:
    def __init__(self,
                 account_data: str) -> None:
        if bip39.Bip39MnemonicValidator().IsValid(mnemonic=account_data):
            account: LocalAccount = Account.from_mnemonic(mnemonic=account_data)
            self.account: AccountData = AccountData(
                address=account.address,
                private_key=account.key.hex(),
                mnemonic=account_data
            )

        else:
            try:
                account: LocalAccount = Account.from_key(private_key=account_data)

                self.account: AccountData = AccountData(
                    address=account.address,
                    private_key=account.key.hex(),
                )

            except ValueError:
                try:
                    self.account: AccountData = AccountData(
                        address=w3.to_checksum_address(value=account_data)
                    )

                except ValueError:
                    raise ValueError('Wrong Account Data')

    async def check_eligible(self,
                             client: aiohttp.ClientSession) -> bool:
        while True:
            response_text: None = None

            try:
                r: aiohttp.ClientResponse = await client.get(
                    url='https://api-ribbon.vercel.app/api/aevo/check-eligibility',
                    params={
                        'address': self.account.address
                    }
                )

                response_text: str = await r.text()
                response_json: dict = await r.json(content_type=None)

                return response_json['airdrop']

            except Exception as error:
                if response_text:
                    logger.error(f'{self.account.address} | Unexpected Error When Getting Proof: {error}, '
                                 f'repsponse: {response_text}')

                else:
                    logger.error(f'{self.account.address} | Unexpected Error When Getting Proof: {error}')

    async def start_checker(self,
                            client: aiohttp.ClientSession) -> None:
        is_eligible: bool = await self.check_eligible(client=client)

        if is_eligible:
            logger.success(f'{self.account.address} | Eligible')

            async with asyncio.Lock():
                await append_file(file_path='result/with_tokens.txt',
                                  file_content=(f'{self.account.address}' + f" | {self.account.private_key}"
                                                if self.account.private_key
                                                else "" + f" | {self.account.mnemonic}"
                                  if self.account.mnemonic else "") + "\n")

            return

        logger.error(f'{self.account.address} | Not Eligible')


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
