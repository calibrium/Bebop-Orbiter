from os import sys
import random
import time
from typing import Literal, Optional, Union
import requests
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from eth_account.messages import SignableMessage, encode_structured_data
from hexbytes import HexBytes
from loguru import logger
from requests import Response
from web3 import Web3
from web3.contract.contract import Contract, ContractFunction
from web3.types import BlockData, Nonce, TxReceipt, Wei
from data.data import Data
from modules.utils import wrapper
from config import Cfg


class Transaction:
    def __init__(self, walletBebop, proxy_web3) -> None:
        self.proxy_web3 = proxy_web3
        self.walletBebop = walletBebop
   

    def _runSwap(self, repeat_count, isSwapWethToToken, proxy, tokens, amounts):
        
        random_sleep = random.randint(Cfg.sleep_range[0], Cfg.sleep_range[1])
        
        logger.debug(
            f"{self.walletBebop.wallet_address} - Спим {random_sleep} секунд(ы) перед стартом | Круг {repeat_count[0]}/{repeat_count[1]}"
        )
        
        time.sleep(random_sleep)

        if isSwapWethToToken == True:
            self.ethereum_amount = amounts[self.walletBebop.WETH]
            if self._isEnouthWethBalance() == False : sys.exit()
        
            tokens.printTokensSwap()

            quote = self._getQuote(path=tokens.tokens, amounts=amounts, proxy=proxy)
        
            if quote == False: return False
            
            signature = self._setSignMsg(quote=quote)
            
            if signature == False: return False

            for token in tokens.tokens["tokens_from"]:
                token_contract: Contract = self.walletBebop.web3.eth.contract(
                    address=token, abi=Data.Abi.erc20
                )

                allowance: Wei = token_contract.functions.allowance(
                    self.walletBebop.wallet_address, Data.Bebop.router
                ).call()

                if allowance <= amounts[token]:
                    approve: ContractFunction = token_contract.functions.approve(
                        Data.Bebop.router, amounts[token]
                    )

                    proccess_approve: bool = self._processTransaction(prepared_call=approve)

                    if proccess_approve is not True:
                        return False
                
            random_timing = random.randint(Cfg.sleep_range_between_actions[0], Cfg.sleep_range_between_actions[1])
        
            logger.info(f"{self.walletBebop.wallet_address} - Спим перед свапом {random_timing} секунд")
            
            time.sleep(random_timing)
            
            proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy is not None else None
        
            if self._check_gas() == False: return False
            
            order_response: Response = requests.post(
                    url=f"https://api.bebop.xyz/pmm/{Data.ChainId.chain_name[self.walletBebop.chain_id]}/v3/order",
                    json={
                    "signature": signature.signature.hex(),  # type: ignore
                    "quote_id": quote["quoteId"],
                    },
                    proxies=proxy_dict
                    )

            logger.info(
                f"{self.walletBebop.wallet_address} - Статус ответа ордера: {order_response.status_code} | Сообщение ордера: {order_response.text}"  # noqa: E501
            )

            if order_response.status_code != 200:
                return False

            verify_tx: bool = self._verify_tx(tx_hash=order_response.json()["txHash"])

            if verify_tx is not True:
                logger.error(
                    f"{self.walletBebop.wallet_address} - Ошибка на свапе | Круг {self.repeat_number[0]}/{self.repeat_number[1]}"  # type: ignore
                )
                return False
        
            logger.success(
                f"{self.walletBebop.wallet_address} - Успешно свапнули | Круг {self.repeat_number[0]}/{self.repeat_number[1]}" # type: ignore
            )
            #ебануть с эфирусуом
            if isSwapWethToToken == True:
                return True

            weth_balance: Union[Wei, Literal[False]] = self._get_weth_balance()

            if weth_balance is False:
                logger.error(
                    f"{self.walletBebop.wallet_address} - Ошибка получения баланса WETH | Круг {self.repeat_number[0]}/{self.repeat_number[1]}" # type: ignore
                )

                return False

            unwrap_ether: bool = self._unwrap_ether(eth_amount=weth_balance)

            if unwrap_ether is not True:
                logger.error(
                    f"{self.walletBebop.wallet_address} - Ошибка анврапа WETH | Круг {self.repeat_number[0]}/{self.repeat_number[1]}" # type: ignore
            )

                return False

            return True


    def swap(self, balance_percent, repeat_count, isSwapWethToToken, proxy, tokens):
        tokens.setRandomTokensSwap(isSwapWethToToken)
        amounts = tokens.getAmountTokens(balance_percent, isSwapWethToToken)
        
        self.repeat_number = repeat_count

        for x in range(Cfg.retry_bebop):  
            if self._runSwap(repeat_count, isSwapWethToToken, proxy, tokens, amounts) == False:
                logger.error(
                    f"{self.wallet_address} - Ошибка свапа | Попытка {x+1}/{Cfg.retry_bebop}"
                )
            else:
                return True
            
        sys.exit()
            

    def _get_weth_balance(self) -> Union[Wei, Literal[False]]:
        return self.walletBebop.weth_contract.functions.balanceOf(self.walletBebop.wallet_address).call()

    def _isEnouthWethBalance(self) -> bool:
       
        weth_balance: Union[Wei, Literal[False]] = self._get_weth_balance()

        eth_amount_gwei = round(Web3.from_wei(weth_balance, "ether"), 4)

        logger.debug(f"{self.walletBebop.wallet_address} - Баланс Weth: {eth_amount_gwei} | Круг {self.repeat_number[0]}/{self.repeat_number[1]}") # type: ignore

        if weth_balance is False:
            return False

        if weth_balance < self.ethereum_amount:
            get_weth: bool = self._wrap_ether(
                eth_amount=int(self.ethereum_amount - weth_balance)
            )

            if get_weth is False:
                logger.error(
                    f"{self.walletBebop.wallet_address} - Врап на WETH: {get_weth} | Круг {self.repeat_number[0]}/{self.repeat_number[1]}" # type: ignore
                )

                return False
        return True


    @wrapper.error_handler
    def _wrap_ether(self, eth_amount: Wei) -> bool:
        prepared_call = self.walletBebop.weth_contract.functions.deposit()

        eth_amount_gwei = round(Web3.from_wei(eth_amount, "ether"), 4)

        logger.info(f"{self.walletBebop.wallet_address} - Делаем обертывание {eth_amount_gwei} эфира | Круг {self.repeat_number[0]}/{self.repeat_number[1]}") # type: ignore
        
        return self._processTransaction(prepared_call=prepared_call, eth_amount=eth_amount)

    @wrapper.error_handler
    def _unwrap_ether(self, eth_amount: Wei) -> bool:
        prepared_call = self.weth_contract.functions.withdraw(eth_amount)

        eth_amount_gwei = round(Web3.from_wei(eth_amount, "ether"), 4)

        logger.info(f"{self.walletBebop.wallet_address} - Анврап {eth_amount_gwei} эфира | Круг {self.repeat_number[0]}/{self.repeat_number[1]}") # type: ignore

        return self._processTransaction(prepared_call=prepared_call)

    @wrapper.error_handler
    def _getQuote(self, path: dict, amounts: dict, proxy: Optional[str]) -> Union[dict, Literal[False]]:
        buy_tokens = ",".join(path["tokens_to"])
        sell_tokens = ",".join(path["tokens_from"])
        sell_amounts = ",".join(str(amount) for amount in amounts.values())

        params = {
            "buy_tokens": buy_tokens,
            "sell_tokens": sell_tokens,
            "sell_amounts": sell_amounts,
            "taker_address": self.walletBebop.wallet_address,
            "receiver_address": self.walletBebop.wallet_address,
            "source": "bebop",
            "approval_type": "Standard",
            "buy_tokens_ratios": self._getTokensRatios(path=path)
        }

        if params["buy_tokens"] == self.walletBebop.WETH:
            del(params["buy_tokens_ratios"])

        proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy is not None else None

        if proxy is not None:
            logger.warning(f"Прокси для запроса к API BEBOP: {proxy} для кошелька {self.walletBebop.wallet_address}")

        response: Response = requests.get(
            url=f"https://api.bebop.xyz/pmm/{Data.ChainId.chain_name[self.walletBebop.chain_id]}/v3/quote",
            headers=Data.Net.headers,
            params=params,
            proxies=proxy_dict
        )

        maybeError = response.json()
        for x in maybeError:
            if x == 'error':
                logger.error(
                    f"{self.walletBebop.wallet_address} - Ошибка получения bebop data | Ошибка: {maybeError['error']['errorCode']} | Ответ Api: {maybeError['error']['message']}"  # noqa: E501
                )
                return False



        if response.status_code == 200:
            return response.json()

        logger.error(
            f"{self.walletBebop.wallet_address} - Ошибка получения bebop data | Статус: {response.status_code} | Ответ Api: {response.text}"  # noqa: E501
        )
        
        logger.debug(f"{self.walletBebop.wallet_address} - Quote bebop data: {self.quote}")

        return False

    @wrapper.error_handler
    def _processTransaction(self, prepared_call: ContractFunction, eth_amount: Wei = 0) -> bool: #type: ignore
        
        nonce: Nonce = self.walletBebop.web3.eth.get_transaction_count(
            self.walletBebop.wallet_address  # type: ignore
        )

        random_timing = random.randint(Cfg.sleep_range_between_actions[0], Cfg.sleep_range_between_actions[1])

        logger.info(f"{self.walletBebop.wallet_address} - Спим {random_timing} секунд перед выполнением транзакции")
        time.sleep(random_timing)
        
        self._check_gas()

        gas: int = prepared_call.estimate_gas(
            {
                "chainId": self.walletBebop.chain_id,
                "from": self.walletBebop.wallet_address,
                "nonce": nonce,
                "value": eth_amount,
            }
        )

        current_gwei: Wei = int(self.walletBebop.web3.eth.gas_price * 1.1)  # type: ignore

        builded_tx: dict = prepared_call.build_transaction(
            {
                "chainId": self.walletBebop.chain_id,
                "from": self.walletBebop.wallet_address,
                "nonce": nonce,
                "gasPrice": current_gwei,
                "gas": gas,
                "value": eth_amount,
            }
        )  # type: ignore

        if self.walletBebop.chain_id != 137:  # Polygon
            del builded_tx["gasPrice"]

            block_data: BlockData = self.walletBebop.web3.eth.get_block(self.walletBebop.web3.eth.block_number)
            builded_tx["maxFeePerGas"] = current_gwei
            builded_tx["maxPriorityFeePerGas"] = block_data["baseFeePerGas"]  # type: ignore  # noqa: E501

        signed_txn: SignedTransaction = self.walletBebop.web3.eth.account.sign_transaction(
            builded_tx, self.walletBebop.evm_private_key
        )

        tx_hash: str = self.walletBebop.web3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()

        return self._verify_tx(tx_hash=tx_hash)
    
    @wrapper.error_handler
    def _setSignMsg(self, quote: dict) -> None:
        if len(quote["buyTokens"]) == 1 and len(quote["sellTokens"]) == 1:
            try:
                if len(quote["buyTokens"]) == 1:
                    to_sign_data = quote["toSign"]
            
                    domain_data = Data.EIP712signatureSingleOrder.bebop["domain"]
                    message_data = Data.EIP712signatureSingleOrder.bebop["message"]

                    domain_data["chainId"] = self.walletBebop.chain_id
                    domain_data["verifyingContract"] = Data.Bebop.router
            
                    message_data.update(
                        {
                            "partner_id": to_sign_data["partner_id"],
                            "expiry": to_sign_data["expiry"],
                            "taker_address": to_sign_data["taker_address"],
                            "maker_address": to_sign_data["maker_address"],
                            "maker_nonce": int(to_sign_data["maker_nonce"]),
                            "taker_token": to_sign_data["taker_token"],
                            "maker_token": to_sign_data["maker_token"],
                            "taker_amount": int(to_sign_data["taker_amount"]),
                            "maker_amount": int(to_sign_data["maker_amount"]),
                            "receiver": quote["receiver"],
                            "packed_commands":int(to_sign_data["packed_commands"]),
                        }
                    )
            except KeyError:
                logger.error(
                    f'Что-то пошло не так с bebop quote data: {quote}'  # noqa: E501
                )

                sys.exit()
            
            Data.EIP712signatureSingleOrder.bebop.update(
                {"domain": domain_data, "message": message_data}
            )

            enocded_msg: SignableMessage = encode_structured_data(
                primitive=Data.EIP712signatureSingleOrder.bebop,
            )

            return Account.sign_message(enocded_msg, self.walletBebop.evm_private_key)

        try:
            quote["toSign"]["taker_amounts"] = [
                int(sublist) for sublist in quote["toSign"]["taker_amounts"]
            ]
            quote["toSign"]["maker_amounts"] = [
                int(sublist) for sublist in quote["toSign"]["maker_amounts"]
            ]
            
            to_sign_data = quote["toSign"]
            domain_data = Data.EIP712signature.bebop["domain"]
            message_data = Data.EIP712signature.bebop["message"]

            domain_data["chainId"] = self.walletBebop.chain_id
            domain_data["verifyingContract"] = Data.Bebop.router
            
            message_data.update(
                {
                    "partner_id": to_sign_data["partner_id"],
                    "expiry": to_sign_data["expiry"],
                    "taker_address": to_sign_data["taker_address"],
                    "maker_address": to_sign_data["maker_address"],
                    "maker_nonce": int(to_sign_data["maker_nonce"]),
                    "taker_tokens": to_sign_data["taker_tokens"],
                    "maker_tokens": to_sign_data["maker_tokens"],
                    "taker_amounts": to_sign_data["taker_amounts"],
                    "maker_amounts": to_sign_data["maker_amounts"],
                    "receiver": quote["receiver"],
                    "commands": Web3.to_bytes(hexstr=to_sign_data["commands"]),
                }
            )
        except KeyError:
            logger.error(
                f'Что-то пошло не так с bebop quote data: {quote}'  # noqa: E501
            )
            logger.debug(f"{self.walletBebop.wallet_address} - Bebop подпись: {self.__name__}")
            sys.exit()

        Data.EIP712signature.bebop.update(
            {"domain": domain_data, "message": message_data}
        )

        enocded_msg: SignableMessage = encode_structured_data(
            primitive=Data.EIP712signature.bebop,
        )

        return Account.sign_message(enocded_msg, self.walletBebop.evm_private_key)

    @wrapper.error_handler
    def _verify_tx(self, tx_hash: HexBytes) -> bool:
        logger.info(
            f"{self.walletBebop.wallet_address} - проверяем статус транзакции: {tx_hash}"  # noqa: E501
        )

        tx_receipt: TxReceipt = self.walletBebop.web3.eth.wait_for_transaction_receipt(
            transaction_hash=tx_hash, timeout=300
        )

        if tx_receipt.get("status") is not None and tx_receipt.get("status") == 1:
            logger.success(f"{self.walletBebop.wallet_address} - успех {tx_hash}")
            return True

        logger.error(f"{self.walletBebop.wallet_address} ошибка {tx_hash}")

        return False
    
    @staticmethod
    def _getTokensRatios(path: dict) -> str:
        token_ratio = None

        if len(path["tokens_to"]) == 1:
            token_ratio = "1"
        else:
            total_sum = 0
            ratios = [round(random.uniform(0, 1 - total_sum), 2) for _ in range(len(path["tokens_to"]) - 1)]
            ratios.append(round(1 - sum(ratios), 2))

            token_ratio = ",".join(map(str, ratios))

        return token_ratio

    @wrapper.error_handler
    def _check_gas(self) -> None:
        if Cfg.gas_limit is None or Cfg.ethereum_rpc is None:
            return
        
        local_web3 = Web3(Web3.HTTPProvider(Cfg.ethereum_rpc, request_kwargs={"proxies":{'https' : self.proxy_web3, 'http' : self.proxy_web3 }}))

        if local_web3.is_connected() is False:
            return

        if local_web3.eth.chain_id != 1:
            return

        while True:
            current_gas = local_web3.eth.gas_price

            if current_gas > local_web3.to_wei(Cfg.gas_limit, 'gwei'):
                logger.info(
                    f"{self.walletBebop.wallet_address} - Газ сейчас: {local_web3.from_wei(current_gas, 'gwei')}, Максимальный газ: {Cfg.gas_limit}, спим 10 секунд"
                )
                
                time.sleep(10)

            else:
                logger.success(f"{self.walletBebop.wallet_address} - Газ ниже установленного значения!")
                break
    





