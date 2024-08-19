from web3.middleware import geth_poa_middleware
from random import randint
from typing import Union
from time import sleep
from web3 import Web3

from modules.utils import logger, sleeping
from config import Cfg


class Wallet:
    def __init__(self, privatekey: str, proxy_web3):
        self.privatekey = privatekey
        self.account = Web3().eth.account.from_key(privatekey)
        self.address = self.account.address
        self.proxy_web3 = proxy_web3


    def get_web3(self, chain_name: str):
        web3 = Web3(Web3.HTTPProvider(Cfg.RPCs[chain_name], request_kwargs={"proxies":{'https' : self.proxy_web3, 'http' : self.proxy_web3 }}))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3


    def wait_for_gwei(self):
        for chain_data in [
            {'chain_name': 'ethereum', 'max_gwei': Cfg.max_gwei}
        ]:
            first_check = True
            while True:
                try:
                    new_gwei = round(self.get_web3(chain_name=chain_data['chain_name']).eth.gas_price / 10 ** 9, 2)
                    if new_gwei < chain_data["max_gwei"]:
                        if not first_check: logger.debug(f'{self.address} - Новый {chain_data["chain_name"].title()} gwei: {new_gwei}')
                        break
                    sleep(5)
                    if first_check:
                        first_check = False
                        logger.debug(f'{self.address} - Ожидаем gwei {chain_data["chain_name"].title()} хотя бы {chain_data["max_gwei"]}. Сейчас: {new_gwei}')
                except Exception as err:
                    logger.warning(f'{self.address} - {chain_data["chain_name"].title()} ожидание gwei завершилось ошибкой: {err}')
                    sleeping(10)


    def get_gas(self, chain_name, increasing_gwei=0):
        max_priority = 0 if chain_name == "zksync" else int(self.get_web3(chain_name=chain_name).eth.max_priority_fee * (Cfg.gwei_multiplier + increasing_gwei))
        last_block = self.get_web3(chain_name=chain_name).eth.get_block('latest')
        base_fee = last_block['baseFeePerGas']
        block_filled = last_block['gasUsed'] / last_block['gasLimit'] * 100
        if block_filled > 50: base_fee *= 1.127
        max_fee = int(base_fee + max_priority)

        return {'maxPriorityFeePerGas': max_priority, 'maxFeePerGas': max_fee}


    def approve(self, chain_name: str, token_name: str, spender: str, amount=None, value=None, retry=0):
        try:
            web3 = self.get_web3(chain_name=chain_name)
            spender = web3.to_checksum_address(spender)
            token_contract = web3.eth.contract(address=web3.to_checksum_address(Cfg.TOKEN_ADDRESSES[token_name]),
                                         abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]')

            decimals = token_contract.functions.decimals().call()
            if amount:
                value = int(amount * 10 ** decimals)
                new_amount = round(amount * randint(10, 40), 5)
                new_value = int(new_amount * 10 ** decimals)
            else:
                new_value = int(value * randint(10, 40))
                new_amount = round(new_value / 10 ** decimals, 5)
            module_str = f'approve {new_amount} {token_name} to {spender}'

            allowance = token_contract.functions.allowance(self.address, spender).call()
            if allowance < value:
                tx = token_contract.functions.approve(spender, new_value)
                tx_hash = self.sent_tx(chain_name=chain_name, tx=tx, tx_label=module_str)
                sleeping(Cfg.sleep_after_tx)
                return tx_hash
        except Exception as error:
            if retry < Cfg.retry:
                logger.error(f'{self.address} - {module_str} | {error}')
                sleeping(10)
                self.approve(chain_name=chain_name, token_name=token_name, spender=spender, amount=amount, value=value, retry=retry+1)
            else:
                logger.info(f'{self.address} - ошибка approve?\n')
                raise ValueError(f'{module_str}: {error}')


    def sent_tx(self, chain_name: str, tx, tx_label, tx_raw=False, value=0, increasing_gwei=0):
        try:
            web3 = self.get_web3(chain_name=chain_name)
            if not tx_raw:
                tx_completed = tx.build_transaction({
                    'from': self.address,
                    'chainId': web3.eth.chain_id,
                    'nonce': web3.eth.get_transaction_count(self.address),
                    'value': value,
                    **self.get_gas(chain_name=chain_name, increasing_gwei=increasing_gwei),
                })
                tx_completed['gas'] = int(int(tx_completed['gas']) * 1.1)
            else:
                tx_completed = tx

            signed_tx = web3.eth.account.sign_transaction(tx_completed, self.privatekey)
            raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = web3.to_hex(raw_tx_hash)
            tx_link = f'{Cfg.chains_data[chain_name]["explorer"]}{tx_hash}'
            logger.debug(f'{self.address} -  {tx_label} транзакция отправлена: {tx_link}')

            status = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=int(Cfg.to_wait_tx * 60)).status

            if status == 1:
                logger.info(f'{self.address} - {tx_label} транзакция завершилась успешно\n')
                return tx_hash
            else:
                logger.info(f'{self.address} - {tx_label} транзакция завершилась ошибкой\n')
                raise ValueError(f'{tx_label} tx failed: {tx_link}')
        except Exception as err:
            if "replacement transaction underpriced" in str(err) or "not in the chain after" in str(err):
                logger.warning(f'{self.address} - {tx_label} | транзакция не была отправлена, повышение gwei')
                return self.sent_tx(chain_name=chain_name, tx=tx, tx_label=tx_label, tx_raw=tx_raw, value=value, increasing_gwei=increasing_gwei + 0.05)
            elif tx_raw: value = tx_completed.get('value')

            try: encoded_tx = f'\n{tx_completed._encode_transaction_data()}'
            except: encoded_tx = ''
            raise ValueError(f'failed: "{err}", value: {value};{encoded_tx}')


    def get_balance(self, chain_name: str, token_name=False, token_address=False, human=False):
        web3 = self.get_web3(chain_name=chain_name)
        if token_name: contract = token_address = Cfg.TOKEN_ADDRESSES[token_name]
        if token_address: contract = web3.eth.contract(address=web3.to_checksum_address(token_address),
                                                       abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]')

        while True:
            try:
                if token_address: balance = contract.functions.balanceOf(self.address).call()
                else: balance = web3.eth.get_balance(self.address)

                if not human: return balance

                decimals = contract.functions.decimals().call() if token_address else 18
                return balance / 10 ** decimals

            except Exception as err:
                logger.warning(f'{self.address} - Ошибка баланса: {err}')
                sleep(5)


    def wait_balance(self, chain_name: str, needed_balance: Union[int, float], only_more: bool = False):
        " needed_balance: human digit "
        if only_more: logger.debug(f'{self.address} - Ожидание баланса больше чем {round(needed_balance, 6)} ETH в {chain_name.upper()}')
        else: logger.debug(f'{self.address} - Ожидаем {round(needed_balance, 6)} ETH баланс в {chain_name.upper()}')
        while True:
            try:
                new_balance = self.get_balance(chain_name=chain_name, human=True)
                if only_more: status = new_balance > needed_balance
                else: status = new_balance >= needed_balance
                if status:
                    logger.debug(f'{self.address} - Новый баланс: {round(new_balance, 6)} ETH\n')
                    return new_balance
                sleep(5)
            except Exception as err:
                logger.warning(f'{self.address} - Ожидание баланса завершилось ошибкой: {err}')
                sleep(10)


    def get_token_decimals(self, chain_name: str, token_name: str):
        if token_name == 'ETH': return 18

        web3 = self.get_web3(chain_name=chain_name)
        token_contract = web3.eth.contract(address=web3.to_checksum_address(Cfg.TOKEN_ADDRESSES[token_name]),
                                           abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]')
        return token_contract.functions.decimals().call()


    def get_human_token_amount(self, chain_name: str, token_name: str, value: Union[int, float], human=True):
        decimals = self.get_token_decimals(chain_name=chain_name, token_name=token_name)

        if human: return round(value / 10 ** decimals, 7)
        else: return int(value * 10 ** decimals)

