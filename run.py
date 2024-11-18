global active_accounts
import asyncio
import random
import signal
import sys
from asyncio import Lock
from loguru import logger
from loader import config, semaphore
from core.bot import Bot
from core.auth import ClientAuth
import models.config1
from utils import export_results, setup, export_statistics
from console import Console

active_accounts = 0
active_accounts_lock = Lock()


async def process_registration(account: models.config1.Account) -> tuple[str, str, bool]:
    async with semaphore:
        if config.delay_before_start.min > 0 and config.delay_before_start.max > 0:
            delay = random.randint(config.delay_before_start.min, config.delay_before_start.max)
            logger.info(f'Account: {account.email} | Sleeping for {delay} seconds before starting...')
            await asyncio.sleep(delay)
        bot = Bot(account)
        result = await bot.process_registration()  # Added parentheses
        await bot.close_session()
        return (account.email, account.password, result)


async def process_verify_accounts(account: models.config1.Account) -> tuple[str, str, bool]:
    async with semaphore:
        if config.delay_before_start.min > 0 and config.delay_before_start.max > 0:
            delay = random.randint(config.delay_before_start.min, config.delay_before_start.max)
            logger.info(f'Account: {account.email} | Sleeping for {delay} seconds before starting...')
            await asyncio.sleep(delay)
        bot = Bot(account)
        result = await bot.process_verify_email()  # Added parentheses
        await bot.close_session()
        return (account.email, account.password, result)


async def process_farming(account: models.config1.Account) -> None:
    global active_accounts
    if config.delay_before_start.min > 0 and config.delay_before_start.max > 0:
        delay = random.randint(config.delay_before_start.min, config.delay_before_start.max)
        logger.info(f'Account: {account.email} | Sleeping for {delay} seconds before starting...')
        await asyncio.sleep(delay)
    async with active_accounts_lock:
        active_accounts += 1
        logger.info(f'Active accounts: {active_accounts}')
    try:
        bot = Bot(account)
        await bot.process_farming()
    except Exception as e:
        logger.error(f'Account: {account.email} | An error occurred during farming: {e}')
    finally:
        async with active_accounts_lock:
            active_accounts -= 1
            logger.info(f'Active accounts: {active_accounts}')


async def process_multiple_farming(account: models.config1.MultipleAccount) -> None:
    global active_accounts
    if config.delay_before_start.min > 0 and config.delay_before_start.max > 0:
        delay = random.randint(config.delay_before_start.min, config.delay_before_start.max)
        logger.info(f'Account: {account.email} | Sleeping for {delay} seconds before starting...')
        await asyncio.sleep(delay)
    async with active_accounts_lock:
        active_accounts += 1
        logger.info(f'Active accounts: {active_accounts}')
    try:
        bot = Bot(account)
        await bot.perform_multiple_farming_actions()
    except Exception as e:
        logger.error(f'Account: {account.email} | An error occurred: {e} | Stopped farming')
    finally:
        async with active_accounts_lock:
            active_accounts -= 1
            logger.info(f'Active accounts: {active_accounts}')


async def process_export_statistics(account: models.config1.Account) -> dict:
    async with semaphore:
        if config.delay_before_start.min > 0 and config.delay_before_start.max > 0:
            delay = random.randint(config.delay_before_start.min, config.delay_before_start.max)
            logger.info(f'Account: {account.email} | Sleeping for {delay} seconds before starting...')
            await asyncio.sleep(delay)
        bot = Bot(account)
        user_info = await bot.process_get_user_info()
        await bot.close_session()
        return user_info


async def cleanup(auth_client: ClientAuth):
    await auth_client.deactivate_session()


async def run(auth_client):
    try:
        while True:
            Console().build()
            if config.module == 'register':
                if not config.accounts_to_register:
                    logger.error('No accounts to register')
                else:
                    tasks = [asyncio.create_task(process_registration(account)) for account in
                             config.accounts_to_register]
                    results = await asyncio.gather(*tasks)
                    export_results(results, 'register')
            elif config.module == 'verify':
                if not config.accounts_to_verify:
                    logger.error('No accounts to verify')
                else:
                    tasks = [asyncio.create_task(process_verify_accounts(account)) for account in
                             config.accounts_to_verify]
                    results = await asyncio.gather(*tasks)
                    export_results(results, 'verify')
            elif config.module == 'farm':
                if not config.accounts_to_farm:
                    logger.error('No accounts to farm')
                else:
                    random.shuffle(config.accounts_to_farm)
                    tasks = [asyncio.create_task(process_farming(account)) for account in config.accounts_to_farm]
                    await asyncio.gather(*tasks)
            elif config.module == 'multiple_farm':
                if not config.accounts_to_multiple_farm:
                    logger.error('No accounts to multiple farm')
                else:
                    logger.info(f'Loaded +- {len(config.accounts_to_multiple_farm[0].proxies)} proxies per account\n\n')
                    await asyncio.sleep(3)
                    random.shuffle(config.accounts_to_multiple_farm)
                    tasks = [asyncio.create_task(process_multiple_farming(account)) for account in
                             config.accounts_to_multiple_farm]
                    await asyncio.gather(*tasks)
            elif config.module == 'export_statistics':
                if not config.accounts_to_farm:
                    logger.error('No accounts to export statistics')
                else:
                    tasks = [asyncio.create_task(process_export_statistics(account)) for account in
                             config.accounts_to_farm]
                    users_data = await asyncio.gather(*tasks)
                    export_statistics(users_data)
                    break
            elif config.module == 'exit':
                break
            input('\n\nPress Enter to continue...')
    except Exception as err:
        logger.debug(f'An error occurred: {err}')
    finally:
        await cleanup(auth_client)


async def main():
    auth_client = ClientAuth()
    status = await auth_client.run()
    if not status:
        return
    try:
        await run(auth_client)
    except asyncio.CancelledError:
        logger.info('Main task was cancelled')
    except Exception as e:
        logger.error(f'An error occurred: {e}')
    finally:
        await cleanup(auth_client)


def handle_interrupt(signum, frame):
    logger.info('Received interrupt signal. Cancelling tasks...')
    for task in asyncio.all_tasks(loop=asyncio.get_event_loop()):
        try:
            task.cancel()
        except asyncio.CancelledError:
            continue


if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        setup()
    signal.signal(signal.SIGINT, handle_interrupt)
    signal.signal(signal.SIGTERM, handle_interrupt)
    try:
        asyncio.run(main())
    except Exception as error:
        logger.debug(f'An error occurred: {error}')
    input('\n\nPress Enter to exit...')