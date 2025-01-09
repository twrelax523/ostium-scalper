from web3 import Web3
from .exceptions import NetworkError
import time
from datetime import datetime
from .abi.faucet_abi import faucet_abi  # Import the ABI


class Faucet:
    def __init__(self, w3: Web3, private_key: str, is_testnet: bool) -> None:
        if not is_testnet:
            raise NetworkError("Faucet is only available on testnet")

        self.web3 = w3
        self.private_key = private_key
        self.faucet_address = "0x6830C550814105d8B27bDAEC0DB391cAa7B967c8"
        self.faucet_contract = self.web3.eth.contract(
            address=self.faucet_address,
            abi=faucet_abi
        )

    # ... rest of the class implementation remains the same ...
