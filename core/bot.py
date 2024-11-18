from better_proxy import Proxy
from loader import captcha_solver, config
import models.config1
from utils import *
from .websocket import WebSocketClient
from .api import GradientNetworkAPI
from .exceptions.base import APIError
import asyncio


class Bot(GradientNetworkAPI):
    def __init__(self, account: models.config1.Account | models.config1.MultipleAccount):
        super().__init__(account)

    async def get_recaptcha_token(self) -> str:
        for attempt in range(3):
            logger.info(f'Account: {self.account_data.email} | Solving captcha... (Attempt {attempt + 1})')
            result, status = await captcha_solver.solve_recaptcha()
            if status:
                logger.success(f'Account: {self.account_data.email} | Captcha solved')
                return result
            logger.error(f'Account: {self.account_data.email} | {result} | Retrying...')
            await asyncio.sleep(3)
        raise APIError('Captcha solving failed after 3 attempts')

    async def process_registration(self) -> bool:
        try:
            if not await check_if_email_valid(self.account_data.imap_server, self.account_data.email,
                                              self.account_data.password):
                return False

            logger.info(f'Account: {self.account_data.email} | Registering...')
            tokens = await self.sign_up()
            await self.lookup_sign_up(tokens['idToken'])

            recaptcha_token = await self.get_recaptcha_token()
            self.session.headers['authorization'] = f"Bearer {tokens['idToken']}"
            response = await self.send_email_verification(recaptcha_token)
            if not response or response.get('code', 0) != 200:
                logger.error(f'Account: {self.account_data.email} | Failed to send email verification: {response}')
                return False

            if not await self.verify_email_process():
                return False

            tokens = await self.get_access_token(tokens['refreshToken'])
            self.session.headers['authorization'] = f"Bearer {tokens['access_token']}"
            await self.bind_invite_code(config.invite_code)
            logger.success(f'Account: {self.account_data.email} | Registered successfully')
            return True

        except APIError as error:
            if error.error_message and error.error_message.strip() == 'EMAIL_EXISTS':
                logger.warning(f'Account: {self.account_data.email} | Email already registered')
                return True
            logger.error(
                f'Account: {self.account_data.email} | Registration failed (APIError): {error.error_message or str(error)}')
        except Exception as error:
            logger.error(f'Account: {self.account_data.email} | Registration failed: {error}')

        return False

    async def verify_email_process(self) -> bool:
        code = await check_email_for_code(self.account_data.imap_server, self.account_data.email,
                                          self.account_data.password)
        if code is None:
            logger.error(f'Account: {self.account_data.email} | Failed to get email verification code')
            return False

        await self.verify_email(code)
        logger.success(f'Account: {self.account_data.email} | Email verified')
        return True

    async def process_farming(self):
        try:
            await self.perform_farming_actions()
        except Exception as error:
            logger.error(f'Account: {self.account_data.email} | Unknown exception during farming: {error} | Stopped')

    async def close_session(self):
        try:
            await self.session.close()
        except Exception as error:
            logger.debug(f'Account: {self.account_data.email} | Failed to close session: {error}')

    async def run_websocket_client(self, node_credentials: dict, proxy: Proxy = None):
        client = WebSocketClient(self.account_data, proxy=proxy)
        return await client.connect(client_id=node_credentials['clientid'], username=node_credentials['username'],
                                    password=node_credentials['password'])

    async def verify_node(self, client_id: str):
        try:
            # Node verification logic here
            pass
        except Exception as error:
            logger.error(f'Account: {self.account_data.email} | Failed to verify node: {error}')
        await asyncio.sleep(600)

    async def process_login(self) -> dict:
        try:
            self.session = self.setup_session()

            # Check if the account is a MultipleAccount
            if isinstance(self.account_data, models.config1.MultipleAccount):
                # Handle multiple accounts (e.g., using the first proxy)
                proxy = self.account_data.proxies[0] if self.account_data.proxies else None
            else:
                # Handle single account
                proxy = self.account_data.proxy

            logger.info(
                f"Account: {self.account_data.email} | Logging in... {(f'| Using proxy: {proxy.as_url}' if proxy else '')}")
            response = await self.sign_in()
            logger.info(f'Account: {self.account_data.email} | Successfully logged in')
            return response
        except APIError as error:
            logger.error(
                f"Account: {self.account_data.email} | Login failed: {error} {(f'| Proxy: {proxy.as_url}' if proxy else '')}")
            return {}

    async def process_get_user_info(self) -> dict:
        try:
            if not await self.process_login():
                return {}
            user_info = await self.user_info()
            logger.success(f'Account: {self.account_data.email} | User info fetched')
            return user_info
        except APIError as error:
            if error.error_message and error.error_message.strip() == 'Please verify email first':
                logger.error(f'Account: {self.account_data.email} | Email verification required')
                await export_unverified_account(self.account_data.email, self.account_data.password)
            elif error.error_message and error.error_message.strip() == 'User  doesn\'t exist':
                logger.error(f'Account: {self.account_data.email} | Account does not exist')
                await export_unregistered_account(self.account_data.email, self.account_data.password)
            else:
                logger.error(f'Account: {self.account_data.email} | {error}')
            return {}

    async def process_verify_email(self) -> bool:
        try:
            response = await self.process_login()
            if not response:
                return False

            recaptcha_token = await self.get_recaptcha_token()
            response = await self.send_email_verification(recaptcha_token)
            if not response or response.get('code', 0) != 200:
                logger.error(f'Account: {self.account_data.email} | Failed to send email verification: {response}')
                return False

            code = await check_email_for_code(self.account_data.imap_server, self.account_data.email,
                                              self.account_data.password)
            if code is None:
                logger.error(f'Account: {self.account_data.email} | Failed to get email verification code')
                return False

            await self.verify_email(code)
            await self.bind_invite_code(config.invite_code)
            logger.success(f'Account: {self.account_data.email} | Account verified')
            return True
        except Exception as error:
            logger.error(f'Account: {self.account_data.email} | Email verification failed: {error}')
            return False

    async def perform_farming_actions(self):
        if not await self.process_login():
            return
        node_credentials = await get_node_credentials(self.account_data.email)
        if not node_credentials:
            node_credentials = await self.process_register_node()
            if not node_credentials:
                return
            await update_node_credentials(self.account_data.email, node_credentials['clientid'],
                                          node_credentials['username'], node_credentials['password'])

        websocket_task = asyncio.create_task(self.run_websocket_client(node_credentials))
        await asyncio.sleep(120)
        verify_task = asyncio.create_task(self.verify_node(node_credentials['clientid']))

        while True:
            if websocket_task.done() or websocket_task.cancelled():
                if websocket_task.result() == 'Node disconnected':
                    logger.info(f'Account: {self.account_data.email} | Stopped farming')
                    break
                logger.info(f'Account: {self.account_data.email} | Retrying farming in 10m')
                await asyncio.sleep(600)
                self.session = self.setup_session()
                return await self.perform_farming_actions()
            if verify_task.done() or verify_task.cancelled():
                logger.info(f'Account: {self.account_data.email} | Stopped farming')
                break
            await asyncio.sleep(3)