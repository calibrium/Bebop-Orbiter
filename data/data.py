import json
import os

current_directory = os.getcwd()


class Data:
    class Net:
        headers = {"Content-Type": "application/json"}

    class ChainId:
        ethereum = 1
        polygon = 137
        arbitrum = 42161
        zksync = 324
        taiko = 167000
        base = 8453
        blast = 81457
        optimism = 10
        scroll = 534352

        chain_name = {
            1: "ethereum",
            42161: "arbitrum",
            324: "zksync",
            167000: "taiko",
            8453: "base",
            81457: "blast",
            10: "optimism",
            534352: "scroll"
        }

    class Bebop:
        router = "0xbbbbbBB520d69a9775E85b458C58c648259FAD5F"

        allowed_chain_ids = [1, 42161, 167000, 8453, 81457, 10]  # Ethereum, Polygon, Arbitrum

    class TokenContract:
        tokens = {
            1: { # Ethereum
                "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "CRV": "0xD533a949740bb3306d119CC777fa900bA034cd52",
                "COMP": "0xc00e94Cb662C3520282E6f5717214004A7f26888",
                "BUSD": "0x4Fabb145d64652a948d72533023f6E7A623C7C53",
                "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "SUSHI": "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",
                "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
            },
            42161: {  # Arbitrum
                "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
                "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
                "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8", # Bridged (USDC.e)
            },
            8453: { #Base, dai не работает
                "WETH": "0x4200000000000000000000000000000000000006",
                "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
                "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
            },
            167000: { #taiko
                "WETH": "0xA51894664A773981C6C112C43ce576f315d5b1B6",
                "TAIKO": "0xA9d23408b9bA935c230493c40C73824Df71A0975",
                "USDC": "0x07d83526730c7438048D55A4fc0b850e2aaB6f0b"
            },
            81457: { #blast
                "WETH": "0x4300000000000000000000000000000000000004",
                "USDB": "0x4300000000000000000000000000000000000003",
            },
            10: {
                "WETH": "0x4200000000000000000000000000000000000006",
                "USDC.e": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
                "USDT": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
            }
        }

    class EIP712signature:
        signature_path = os.path.join(
            current_directory, "data", "eip712signature", "bebop_signature.json"
        )

        with open(signature_path, "r") as file:
            bebop = json.load(file)
    
    class EIP712signatureSingleOrder:
        signature_path = os.path.join(
            current_directory, "data", "eip712signature", "bebop_signature_singleOrder.json"
        )

        with open(signature_path, "r") as file:
            bebop = json.load(file)

    class Abi:
        erc20_path = os.path.join(current_directory, "data", "abi", "erc20.json")

        weth_path = os.path.join(current_directory, "data", "abi", "weth.json")

        with open(erc20_path, "r") as file:
            erc20 = json.load(file)

        with open(weth_path, "r") as file:
            weth = json.load(file)
