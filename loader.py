# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: loader.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import asyncio
from utils import load_config
from core.captcha import capsolver

config = load_config()
captcha_solver = capsolver.CapsolverSolver(api_key=config.capsolver_api_key)
semaphore = asyncio.Semaphore(config.threads)