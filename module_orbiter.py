from modules.orbiter import Orbiter
from modules.utils import sleeping, logger
from modules import *
from config import Cfg
from modules.wallet import Wallet


def module_orbiter(private_key: str, from_chain:str, to_chain: str, proxy: str):
    try:
        wallet = Wallet(privatekey=private_key, proxy_web3=proxy)
        print('')
        logger.info(f'{wallet.address} - Starting "most Orbiter"')
        Orbiter(wallet=wallet, from_chain=from_chain, to_chain=to_chain, proxy_web3=proxy)
        

    except Exception as err:
        logger.error(f'{wallet.address} - Account error: {err}')

    finally:
        sleeping(Cfg.sleep_after_acc)

