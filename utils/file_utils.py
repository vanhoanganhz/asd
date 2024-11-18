# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: utils\file_utils.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import json
import os
import csv
from asyncio import Lock
import aiofiles
from loguru import logger
lock = Lock()

def export_results(results: list, module: str) -> None:
    if not os.path.exists('./results'):
        os.makedirs('./results')
    if not os.path.exists('./results/registration_success.txt'):
        open('./results/registration_success.txt', 'w').close()
    if not os.path.exists('./results/registration_failed.txt'):
        open('./results/registration_failed.txt', 'w').close()
    if module == 'register':
        success_txt = open('./results/registration_success.txt', 'a')
        failed_txt = open('./results/registration_failed.txt', 'a')
        for email, account_password, status in results:
            if status:
                success_txt.write(f'{email}:{account_password}\n')
            else:
                failed_txt.write(f'{email}:{account_password}\n')
    elif module == 'verify':
        success_txt = open('./results/verification_success.txt', 'a')
        failed_txt = open('./results/verification_failed.txt', 'a')
        for email, account_password, status in results:
            if status:
                success_txt.write(f'{email}:{account_password}\n')
            else:
                failed_txt.write(f'{email}:{account_password}\n')
    logger.debug('Results exported to results folder')

async def export_unverified_account(email: str, password: str) -> None:
    async with lock:
        if not os.path.exists('./results'):
            os.makedirs('./results')
        if not os.path.exists('./results/unverified_accounts.txt'):
            async with aiofiles.open('./results/unverified_accounts.txt', mode='w') as f:
                await f.write('')
        async with aiofiles.open('./results/unverified_accounts.txt', mode='a') as f:
            await f.write(f'{email}:{password}\n')
        logger.debug('Unverified account exported to results folder')

async def export_unregistered_account(email: str, password: str) -> None:
    async with lock:
        if not os.path.exists('./results'):
            os.makedirs('./results')
        if not os.path.exists('./results/unregistered_accounts.txt'):
            async with aiofiles.open('./results/unregistered_accounts.txt', mode='w') as f:
                await f.write('')
        async with aiofiles.open('./results/unregistered_accounts.txt', mode='a') as f:
            await f.write(f'{email}:{password}\n')
        logger.debug('Unregistered account exported to results folder')

async def get_node_credentials(email: str):
    async with lock:
        async with aiofiles.open('./config/node_credentials.json', mode='r') as f:
            data = await f.read()
            if not data:
                return {}
            else:
                data = json.loads(data)
                return data.get(email, {})

async def update_node_credentials(email: str, client_id: str, username: str, password: str):
    async with lock:
        async with aiofiles.open('./config/node_credentials.json', mode='r') as f:
            data = await f.read()
            if not data:
                data = {}
            else:
                data = json.loads(data)
        data[email] = {'clientid': client_id, 'username': username, 'password': password}
        async with aiofiles.open('./config/node_credentials.json', mode='w') as f:
            await f.write(json.dumps(data, indent=4))

def export_statistics(users_data: list[dict]):
    if not os.path.exists('./results'):
        os.makedirs('./results')
    unique_users = []
    for data in users_data:
        if data and data['id'] not in unique_users:
            unique_users.append(data)
    with open('./results/statistics.csv', 'w', newline='') as file:
        fieldnames = ['ID', 'Username', 'Email', 'Invite code', 'Total points', 'Referrals']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        logger.debug('Exporting statistics to CSV file...')
        for data in unique_users:
            if data:
                writer.writerow({'ID': data['id'], 'Username': data['name'], 'Email': data['email'], 'Invite code': data['code'], 'Total points': int(data['point']['total']) / 100000, 'Referrals': data['stats']['invitee']})
    logger.debug('Export completed successfully.')