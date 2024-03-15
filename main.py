import asyncio
from os import mkdir
from os.path import exists
from sys import stderr

import aiohttp
from loguru import logger
from pyuseragents import random as random_useragent

from core import start_checker
from utils import loader
from os import remove, listdir

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')


async def main() -> None:
    loader.semaphore = asyncio.Semaphore(value=threads)

    async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                verify_ssl=None,
                ssl=False,
                use_dns_cache=False,
                ttl_dns_cache=300,
                limit=None
            ),
            headers={
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'ru,en;q=0.9,vi;q=0.8,es;q=0.7,cy;q=0.6',
                'content-type': 'application/json',
                'origin': 'https://magiceden.io',
                'referer': 'https://magiceden.io/',
                'user-agent': random_useragent()
            }
    ) as client:
        tasks: list[asyncio.Task] = [
            asyncio.create_task(coro=start_checker(account_data=current_account,
                                                   client=client))
            for current_account in accounts_list
        ]

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    if not exists(path='result'):
        mkdir(path='result')

    threads: int = int(input('Threads: '))
    print()

    for current_file in listdir(path='data'):
        with open(file=f'data/{current_file}',
                  mode='r',
                  encoding='utf-8-sig') as file:
            accounts_list: list[str] = [row.strip() for row in file]

        logger.success(f'Successfully Loaded {len(accounts_list)} Accounts')

        try:
            import uvloop

            uvloop.run(main())

        except ModuleNotFoundError:
            asyncio.run(main())

        remove(path=f'data/{current_file}')

    logger.success(f'The Work Has Been Successfully Finished')
    input('\nPress Enter to Exit..')
