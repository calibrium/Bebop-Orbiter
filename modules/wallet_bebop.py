from eth_account import Account
from web3 import Web3
from web3.contract.contract import Contract
from data.data import Data


class WalletBebop:
    def __init__(self, web3_url: str, evm_private_key: str, proxy) -> None:
        self.evm_private_key: str = evm_private_key
        self.web3: Web3 = Web3(Web3.HTTPProvider(web3_url, request_kwargs={"proxies":{'https' : proxy, 'http' : proxy }}))
        self.chain_id: int = self.web3.eth.chain_id
        self.wallet_address: str = Account.from_key(self.evm_private_key).address
        self.WETH: str = Data.TokenContract.tokens[self.chain_id]["WETH"]
        self.weth_contract: Contract = self.web3.eth.contract(
            address = self.web3.to_checksum_address(self.WETH),
            abi = Data.Abi.weth,
        )
        assert (
            self.web3.is_connected() is True
        ), f"Ошибка инициализации web3 с {web3_url}"





