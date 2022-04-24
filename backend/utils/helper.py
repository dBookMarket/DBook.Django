import uuid
from random import random
from web3.auto import w3
from web3 import Web3
from eth_account.messages import encode_defunct
import time


class Helper:

    @staticmethod
    def rand_nonce(digits: int = 7) -> str:
        # return str(int(random() * 10 ** digits))
        return Web3.toHex(Web3.keccak(text=str(int(time.time() * 10 ** digits)))).strip('0x')

    @staticmethod
    def rand_username() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def eth_recover(message: str, signature: str) -> str:
        msg_hash = encode_defunct(text=message)
        signer = w3.eth.account.recover_message(msg_hash, signature=signature)
        return signer

    @staticmethod
    def equal(str1: str, str2: str):
        return str(str1).lower() == str(str2).lower()
