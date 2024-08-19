from random import uniform
from modules.utils import logger, sleeping
from modules.wallet import Wallet
from config import Cfg


class Orbiter(Wallet):
    def __init__(self, wallet: Wallet, from_chain, to_chain, proxy_web3):
        super().__init__(privatekey=wallet.privatekey, proxy_web3=proxy_web3)

        self.from_chain = from_chain
        self.to_chain = to_chain
        
        self.wait_for_gwei()
            
        keep_values_ = Cfg.keep_values[from_chain]
        
        keep_value = round(uniform(keep_values_[0], keep_values_[1]), 4) * 1e18
        self.value = int(self.get_balance(chain_name=self.from_chain) - keep_value)

        self.web3 = self.get_web3(self.from_chain)
        
        self.orbiter_bridge_address = self.web3.to_checksum_address(Cfg.orbiter_adresses[self.from_chain])

        self.value = int(self.value - self.get_tx_cost())
        self.value = int(str(self.value)[:-4] + Cfg.orbiter_codes[self.to_chain])
        if str(self.value)[-4:] != Cfg.orbiter_codes[self.to_chain]:
            raise Exception(f'Bad calculated value for orbiter: {self.value} (code {Cfg.orbiter_codes[self.to_chain]})')
        self.amount = round(self.value / 1e18, 6)

        self.bridge()
            
        sleeping(Cfg.sleep_after_tx)


    def get_tx_cost(self):
        return self.web3.eth.gas_price * self.web3.eth.estimate_gas({'from': self.address, 'to': self.orbiter_bridge_address}) * 2


    def bridge(self, retry=0):
        try:
            module_str = f'orbiter bridge {self.from_chain} {self.amount} ETH -> {self.to_chain}'
            old_balance = self.get_balance(chain_name=self.to_chain, human=True)

            tx = {
                    'from': self.address,
                    'to': self.orbiter_bridge_address,
                    'chainId': self.web3.eth.chain_id,
                    'nonce': self.web3.eth.get_transaction_count(self.address),
                    'value': self.value,
                    **self.get_gas(chain_name=self.from_chain),
                }
            tx['gas'] = self.web3.eth.estimate_gas(tx)

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=tx, tx_label=module_str, tx_raw=True)
            self.wait_balance(chain_name=self.to_chain, needed_balance=old_balance, only_more=True)

            return tx_hash

        except Exception as error:
            logger.error(f'{self.address} - {module_str} | {error} [{retry + 1}/{Cfg.retry}]')
            if retry < Cfg.retry:
                sleeping(10)
                return self.bridge(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
