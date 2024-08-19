from os import sys
import random
import traceback
from modules.utils import wrapper
from loguru import logger
from config import Cfg
from web3 import Web3
from data.data import Data


class Tokens:
    
    def __init__(self, all_tokens, walletBebop) -> None:
        self.all_tokens = all_tokens
        self.tokens = None
        self.walletBebop = walletBebop
    
    def printTokensSwap(self):
        address_to_ticker = {address: ticker for ticker, address in self.all_tokens.items()}

        tokens_from_symbols = [
            address_to_ticker.get(address, address) for address in self.tokens.get("tokens_from", [])
        ]
        
        tokens_to_symbols = [
            address_to_ticker.get(address, address) for address in self.tokens.get("tokens_to", [])
        ]
        
        logger.info(f"{self.walletBebop.wallet_address} - Свапаем с {' '.join(tokens_from_symbols)} на {' '.join(tokens_to_symbols)}")
        
    @wrapper.error_handler
    def getAmountTokens(self, balance_percent, isSwapWethToToken):
        
        total_amounts = {}
        amounts = {}
        
        if isSwapWethToToken == True:
            eth_amount_wei = self.walletBebop.web3.eth.get_balance(self.walletBebop.wallet_address)  # type: ignore
            
            if self._isCorrectAmount(eth_amount_wei, isSwapWethToToken) == False : sys.exit()
            
            total_amounts[self.walletBebop.WETH] = eth_amount_wei
        else:
            for token in self.tokens["tokens_from"]:
                token_instance = self.walletBebop.web3.eth.contract(
                    address=token, abi= Data.Abi.erc20  # type: ignore
                )

                eth_amount_wei = token_instance.functions.balanceOf(self.walletBebop.wallet_address).call()

                if self._isCorrectAmount(eth_amount_wei, isSwapWethToToken) == False : sys.exit()
                
                total_amounts[token] = eth_amount_wei

        for token, amount in total_amounts.items():
            if self._isCorrectAmount(amount, isSwapWethToToken) == False : sys.exit()

            amounts[token] = int(total_amounts[token] * balance_percent)
        
        logger.info(f"{self.walletBebop.wallet_address} - Сумма в токенах которые будем свапать: {amounts}")
        
        return amounts
    
    def _isCorrectAmount(self, amount, flag):
        if flag == True:
            eth_amount = round(Web3.from_wei(amount, "ether"), 4)
        
            if amount < int(Cfg.minimal_balance * 10**18):
                logger.warning(
                    f"{self.walletBebop.wallet_address} - Баланс: {eth_amount} меньше минимально разрешенного баланса: {Cfg.minimal_balance}"  # noqa: E501
                )   
                return False
        else:
            if amount == 0:
                logger.error(f"{self.walletBebop.wallet_address} - Баланс одного из токенов 0")
                return False
            
        return True

    @wrapper.error_handler
    def setRandomTokensSwap(self, isSwapWethToToken) -> dict:
        
        available_tokens = [
            token
            for token in self.all_tokens.values()
            if token != self.walletBebop.WETH
        ]

        if isSwapWethToToken == True:
            try:
                tokens_from_swap = [self.walletBebop.WETH]
                
                if len(available_tokens) == 1:
                    tokens_to_swap = random.sample(available_tokens, 1)
                else:
                    tokens_to_swap = random.sample(available_tokens, Cfg.one_to_many_tokens)
            except ValueError:
                logger.error(f"Переменная 'one_to_many_tokens' не должна превышать доступное количество токенов на сети! На этой сети доступно максимум {len(self.TokenContract.tokens[self.chain_id].keys()) - 1} токена, вы поставили {Cfg.one_to_many_tokens}")
                sys.exit()
            except Exception as e:
                traceback.print_exc()
                logger.error(f"Error occured: {e} in {self.setRandomTokensSwap.__name__}")
                sys.exit()
        else: 
            tokens_from_swap = self.tokens["tokens_to"]
            tokens_to_swap = [self.walletBebop.WETH]
            
        self.tokens = {
            "tokens_from": tokens_from_swap,
            "tokens_to": tokens_to_swap,
        }
    
    # def _isSwapWethToToken(self):
    #     if self.tokens == None:
    #         return True
        
    #     tokens_from = self.tokens["tokens_from"]
    #     asdsf =  self.tokens["tokens_to"] 
    #     for x in tokens_from:
    #         if self.walletBebop.WETH == x:
    #             return True
            
    #     return False
    
    



