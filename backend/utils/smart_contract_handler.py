from web3 import Web3
from django.conf import settings


class PlatformContractHandler(object):

    def __init__(self):
        self.web3 = Web3()
        self.contract = self.web3.eth.contract(address=settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ADDRESS'],
                                               abi=settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ABI'])

    def add_author(self, account_addr: str) -> True:
        """
        Give the user issue permission from contract.
        """
        try:
            txn_hash = self.contract.functions.addAuth(account_addr).transact(
                {'from': settings['CONTRACT_SETTINGS']['ADMIN_ADDRESS']})
        except Exception as e:
            print(f'Exception when calling add_author -> {e}')
            return False
        receipt = self.web3.eth.get_transaction_receipt(txn_hash)
        print(receipt)
        return True
