from modules.tokens import Tokens
import random
from config import Cfg
from typing import Optional
from data.data import Data
from modules.transaction import Transaction
from modules.wallet_bebop import WalletBebop

def module_bebop(
    web3_url: str, private_key: str, balance_percent: float, tokens_from: Optional[list[str]], proxy: Optional[str]
) -> bool:
    proxy_for_web3 = "http://" + proxy
    repeat_count = random.randint(Cfg.repeat_count[0], Cfg.repeat_count[1])
    
    wallet = WalletBebop(web3_url, private_key, proxy_for_web3)
    transaction = Transaction(wallet, proxy_for_web3)
    tokens = Tokens(Data.TokenContract.tokens[wallet.chain_id], wallet)
    
    for repeat in range(repeat_count):
        
        transaction.swap(balance_percent, [repeat+1, repeat_count], True, proxy, tokens)
        
        transaction.swap(0.9999, [repeat+1, repeat_count], False, proxy, tokens)
        
    return True