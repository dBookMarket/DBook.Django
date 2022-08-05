from web3 import Web3
from web3.middleware import geth_poa_middleware
from django.conf import settings


class PlatformContractHandler(object):
    ADMIN_KEY = settings.CONTRACT_SETTINGS['ADMIN_KEY']

    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(settings.CONTRACT_SETTINGS['HTTP_PROVIDER']))
        # Unfortunately, it does deviate from the yellow paper specification,
        # which constrains the extraData field in each block to a maximum of 32-bytes.
        # Geth’s PoA uses more than 32 bytes, so this middleware modifies the block data a bit before returning it.
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.contract = self.web3.eth.contract(address=settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ADDRESS'],
                                               abi=settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ABI'])
        self.admin_account = self.web3.eth.account.from_key(self.ADMIN_KEY)

    def add_author(self, account_addr: str) -> bool:
        """
        Give the user issue permission from contract.
        """
        try:
            # check account address
            account_addr = Web3.toChecksumAddress(account_addr)

            print('admin address ->', self.admin_account.address)
            nonce = self.web3.eth.get_transaction_count(self.admin_account.address)
            transaction = self.contract.functions.addAuth(account_addr).buildTransaction(
                {'from': self.admin_account.address, 'nonce': nonce})
            signed_txn = self.admin_account.sign_transaction(transaction)
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        except Exception as e:
            print(f'Exception when calling add_author -> {e}')
            return False
        self.web3.eth.wait_for_transaction_receipt(txn_hash)
        receipt = self.web3.eth.get_transaction_receipt(txn_hash)
        print(receipt)
        return bool(receipt['status'] == 1)
