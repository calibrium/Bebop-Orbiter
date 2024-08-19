from os import sys
from config import Cfg
from loguru import logger
from random import choice

class Config:
    
    def __init__(self) -> None:
        if self.__isCorrectConfig__() == False: sys.exit()
        self._private_keys = None
        self._proxy_dictionary = None
        self._started_network = None
        self._web3_url = None
        self._from_chain = None
        self._to_chain = None

    def setCfgTransfer(self, i, startedNetwork = None) -> None:
        """
        Set value for web3_url, from_chain, to_chain
        """
        if i == 0 and startedNetwork != None:
            self._web3_url = Cfg.RPCs[startedNetwork]
            self._from_chain = startedNetwork
            self._to_chain = choice(Cfg.to_bridge_chains)
            while self._to_chain == self._from_chain or self._to_chain == 'ethereum':
                self._to_chain = choice(Cfg.to_bridge_chains)
        else:
            previous_from_chain = self._from_chain
            self._from_chain = self._to_chain
            self._web3_url = Cfg.RPCs[self._from_chain]
            self._to_chain = choice(Cfg.to_bridge_chains)
            while self._to_chain == previous_from_chain or self._to_chain == 'ethereum':
                self._to_chain = choice(Cfg.to_bridge_chains)

    def getWeb3Url(self) -> str:
        return self._web3_url
    
    def getFromChain(self) -> str:
        return self._from_chain
    
    def getToChain(self) -> str:
        return self._to_chain

    def getPrivateKeys(self) -> list[str]:
        self._private_keys = self.__getAbstractMethod__("private_keys", self.__isCorrectPrivateKeys__)
        return self._private_keys
        
    def getProxies(self) -> list[str]:
        self._proxy_dictionary = self.__getAbstractMethod__("proxies", self.__isCorrectProxies__, self._private_keys)
        return self._proxy_dictionary
    
    def getStartedNetwork(self) -> list[str]:
        self._started_network = self.__getAbstractMethod__("start_network", self.__isCorrectStartedNetworks__, self._private_keys)
        return self._started_network
    
    def __getAbstractMethod__(self, nameFileTxt, funcIsCorrect, privateKeys = None) -> list[str]:
        try:
            if privateKeys == None:
                with open(f"{nameFileTxt}.txt", "r") as file:
                    private_keys = [key.strip() for key in file.readlines() if key.strip()]
                    if funcIsCorrect(private_keys) == False: sys.exit()
                    return private_keys
                
            with open(f"{nameFileTxt}.txt", "r") as file:
                lineTxtList = [key.strip() for key in file.readlines() if key.strip()]
                if funcIsCorrect(lineTxtList, privateKeys) == False: sys.exit()
                return {pks: lTL for pks, lTL in zip(privateKeys, lineTxtList)}
            
        except FileNotFoundError:
            logger.error(
                f"Файл не найден, пожалуйста, создайте файл '{nameFileTxt}.txt' в директории с проектом"  # noqa: E501
            )
            sys.exit()

    @staticmethod
    def __isCorrectStartedNetworks__(started_network_list, private_keys) -> bool:
        
        if started_network_list == [] or started_network_list is False:
            logger.error("Вы не ввели стартовую сеть!")
            return False

        if len(started_network_list) != len(private_keys):
            logger.error(f"Стартовых сетей должно быть столько же, сколько и праватных ключей! У вас {len(private_keys)} приватных ключей и {len(started_network_list)} прокси")
            return False
        
        return True
      
    @staticmethod
    def __isCorrectPrivateKeys__(private_keys) -> bool:
        if private_keys is False:
            logger.error("Ошибка в 'get_private_keys'")
            return False

        if len(private_keys) == 0:
            logger.warning("Чтобы запустить скрипт в 'private_keys.txt' должно быть не менее 1 приватного ключа")  # noqa: E501
            return False
        
        return True
    
    @staticmethod
    def __isCorrectProxies__(proxy_list, private_keys) -> bool:
        if proxy_list == [] or proxy_list is False:
            logger.error("Вы не добавили прокси!")
            return False

        if len(proxy_list) != len(private_keys):
            logger.error(f"Прокси должно быть столько же, сколько и праватных ключей! У вас {len(private_keys)} приватных ключей и {len(proxy_list)} прокси")
            return False
        
        return True
    
    @staticmethod
    def __isCorrectConfig__() -> bool:
        if Cfg.min_percent > Cfg.max_percent:
            logger.error(
            "Вы не можете поставить 'min_percent' больше чем 'max_percent'!"
        )
            
            return False
    
        if Cfg.max_percent > 100:
            logger.error(
                "Вы не можете поставить 'max_percent' больше чем 100! (Более 99 не рекомендуется)"
            )
        
            return False
    
        if Cfg.tokens_from and Cfg.tokens_to:
            logger.error(
                "Вы не можете поставить сразу 'tokens_from' и 'tokens_to', одна их переменных должна быть 'None'"
            )

            return False
    
        if not isinstance(Cfg.minimal_balance, (int, float)):
            logger.error(
                "Переменная 'minimal_balance' должна быть числом! (int или float)"
            )

            return False

        if isinstance(Cfg.repeat_count, list) is False:
            logger.error(
                "Переменная 'repeat_count' должна быть list"
            )

            return False

        if len(Cfg.repeat_count) != 2:
            logger.error(
                "Переменная 'repeat_count' должна содержать 2 значения [от, до]"
            )

            return False

        for i in Cfg.repeat_count:
            if isinstance(i, int) is False:
                logger.error(
                    "Все значения в 'repeat_count' должны быть целым числом!"
                )

                return False

        if isinstance(Cfg.sleep_range, list) is False:
            logger.error(
                "Переменная 'sleep_range' должна быть list"
            )

            return False

        if len(Cfg.sleep_range) != 2:
            logger.error(
                "Переменная 'sleep_range' должна содержать 2 значения [от, до]"
            )

            return False

        for i in Cfg.sleep_range:
            if isinstance(i, int) is False:
                logger.error(
                    "Все значения в 'sleep_range' должны быть целыми числами!"
                )

                return False
        
        if isinstance(Cfg.sleep_range_between_actions, list) is False:
            logger.error(
                "Переменная 'sleep_range_between_actions' должна быть list"
            )

            return False

        if len(Cfg.sleep_range_between_actions) != 2:
            logger.error(
                "Переменная 'sleep_range_between_actions' должна содержать 2 значения [от, до]"
            )

            return False

        for i in Cfg.sleep_range_between_actions:
            if isinstance(i, int) is False:
                logger.error(
                    "Все значения в 'sleep_range_between_actions' должны быть целыми числами!"
                )

                return False
        
        return True
    


