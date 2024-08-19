from datetime import datetime
from random import randint
from requests import post
from loguru import logger
from time import sleep
from tqdm import tqdm
from web3 import Web3
import sys
import ctypes
import os
import functools
import traceback
from typing import Any, Callable
from loguru import logger
sys.__stdout__ = sys.stdout # error with `import inquirer` without this string in some system


logger.remove()
logger.add(sys.stderr, format="<white>{time:HH:mm:ss}</white> | <level>{message}</level>")
windll = ctypes.windll if os.name == 'nt' else None # for Mac users

class wrapper:
    @staticmethod
    def error_handler(func: Callable) -> Any:
        """Catch errors"""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                traceback.print_exc()
                logger.error(f"Error occured: {e} in {func.__name__}")

                return False

        return wrapper

def sleeping(*timing):
    if type(timing[0]) == list: timing = timing[0]
    if len(timing) == 2: x = randint(timing[0], timing[1])
    else: x = timing[0]
    desc = datetime.now().strftime('%H:%M:%S')
    for _ in tqdm(range(x), desc=desc, bar_format='{desc} | [•] Sleeping {n_fmt}/{total_fmt}'):
        sleep(1)


def get_address(pk: str):
    return Web3().eth.account.from_key(pk).address



