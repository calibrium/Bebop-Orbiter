import random
from loguru import logger
from config import Cfg
from module_bebop import module_bebop
from module_orbiter import module_orbiter
from modules.config_settings import Config


def main() -> None:
    logger.warning("Cкрипт начал работу")
    config = Config()
    
    private_keys = config.getPrivateKeys()
    started_network = config.getStartedNetwork()
    proxies = config.getProxies()
    for key in private_keys:
        for i in range(Cfg.Iteration):
            config.setCfgTransfer(i, started_network[key])
            module_bebop(web3_url=config.getWeb3Url(), 
                         private_key=key,
                         balance_percent=random.uniform(
                             Cfg.balance_percent[0], Cfg.balance_percent[1]
                         ),
                         tokens_from = None,
                         proxy = proxies[key])

            if i+1 == int(Cfg.Iteration):
                continue
            
            module_orbiter(key, config.getFromChain(), config.getToChain(), "http://" + proxies[key])
    
if __name__ == "__main__":
    main()
    
    