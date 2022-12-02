from web3 import Web3
from web3.middleware import geth_poa_middleware
from django.conf import settings
from utils.enums import BlockChainType, TransactionStatus


class PlatformContractHandler(object):
    ADMIN_KEY = settings.CONTRACT_SETTINGS['ADMIN_KEY']
    PLATFORM_KEY = settings.CONTRACT_SETTINGS['PLATFORM_KEY']
    PRECISION = 1_000_000

    def __init__(self, provider: str = settings.CONTRACT_SETTINGS.get('HTTP_PROVIDER')):
        self.admin_account = self.web3.eth.account.from_key(self.ADMIN_KEY)
        self.platform_account = self.web3.eth.account.from_key(self.PLATFORM_KEY)

        self.web3 = Web3(Web3.HTTPProvider(provider))
        # Unfortunately, it does deviate from the yellow paper specification,
        # which constrains the extraData field in each block to a maximum of 32-bytes.
        # Geth’s PoA uses more than 32 bytes, so this middleware modifies the block data a bit before returning it.
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.contract = self.web3.eth.contract(address=settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ADDRESS'],
                                               abi=settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ABI'])

    def to_usdc(self, amount: float) -> int:
        return int(amount * self.PRECISION)

    def to_percent_percent(self, ratio: float) -> int:
        """
        % -> %%
        """
        return int(ratio * 100)

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
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        print(receipt)
        return bool(receipt['status'] == 1)

    def first_trade(self, seller: str, payment: float, buyer: str, token_id: int, amount: int, mint_amount: int = 0):
        """
        trade of the issue from author

        :param seller: str, seller address,
        :param payment: float, payment to seller,
        :param buyer: str, buyer address,
        :param token_id: int, nft id
        :param amount: int, amount of nft to buyer
        :param mint_amount: int, the number of nft to be minted
        """
        print(f'platform address->{self.platform_account.address}')
        # check address
        seller = Web3.toChecksumAddress(seller)
        buyer = Web3.toChecksumAddress(buyer)

        # send transaction
        nonce = self.web3.eth.get_transaction_count(self.platform_account.address)
        transaction = self.contract.functions.runFirstTrade(seller, self.to_usdc(payment), mint_amount,
                                                            buyer, token_id, amount, '0x01').buildTransaction({
            'from': self.platform_account.address, 'nonce': nonce
        })
        signed_txn = self.platform_account.sign_transaction(transaction)
        txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        # get result
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        status = TransactionStatus.SUCCESS.value if receipt['status'] == 1 else TransactionStatus.FAILURE.value

        return {
            'hash': txn_hash.hex(),
            'status': status
        }

    def pay_back(self, to: str, amount: float) -> bool:
        """
        if the transaction is failed, pay back to the buyer.
        :param to: str, buyer address
        :param amount: float, payment for the NFT

        :return: bool
        """
        # check address
        to = Web3.toChecksumAddress(to)

        # send transaction
        txn_hash = self.web3.eth.send_transaction({
            'from': self.admin_account.address,
            'to': to,
            'value': self.to_usdc(amount)
        })
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return receipt['status'] == 1

    def set_token_info(self, token_id: int, author: str, royalty: float, price: float) -> bool:
        """
        :param token_id: int, nft id
        :param author: str, wallet address of author
        :param royalty: float, 0 ~ 100%
        :param price: float, nft price

        :return: bool
        """
        return bool(self.set_token_author(token_id, author) and
                    self.set_token_royalty(token_id, royalty) and
                    self.set_token_price(token_id, price))

    def set_token_price(self, token_id: int, price: float) -> bool:
        try:
            nonce = self.web3.eth.get_transaction_count(self.admin_account.address)
            txn = self.contract.functions.setNftPrice(token_id, self.to_usdc(price)).buildTransaction({
                'from': self.admin_account.address, 'nonce': nonce
            })
            signed_txn = self.admin_account.sign_transaction(txn)
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        except Exception as e:
            print(f'Exception when setting nft price->{e}')
            return False
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return receipt['status'] == 1

    def set_token_author(self, token_id: int, author: str) -> bool:
        try:
            author = Web3.toChecksumAddress(author)

            nonce = self.web3.eth.get_transaction_count(self.admin_account.address)
            txn = self.contract.functions.setPublisherAddress(token_id, author).buildTransaction({
                'from': self.admin_account.address, 'nonce': nonce
            })
            signed_txn = self.admin_account.sign_transaction(txn)
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        except Exception as e:
            print(f'Exception when setting nft price->{e}')
            return False
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return receipt['status'] == 1

    def set_token_royalty(self, token_id: int, royalty: float) -> bool:
        try:
            nonce = self.web3.eth.get_transaction_count(self.admin_account.address)
            txn = self.contract.functions.setPublisherRatio(token_id,
                                                            self.to_percent_percent(royalty)).buildTransaction({
                'from': self.admin_account.address, 'nonce': nonce
            })
            signed_txn = self.admin_account.sign_transaction(txn)
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        except Exception as e:
            print(f'Exception when setting nft price->{e}')
            return False
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return receipt['status'] == 1


class PolygonHandler(PlatformContractHandler):

    def __init__(self, provider: str = settings.CONTRACT_SETTINGS['POLYGON']['PROVIDER']):
        super().__init__(provider)
        self.contract = self.web3.eth.contract(
            address=settings.CONTRACT_SETTINGS['POLYGON']['PLATFORM_CONTRACT_ADDRESS'],
            abi=settings.CONTRACT_SETTINGS['POLYGON']['PLATFORM_CONTRACT_ABI']
        )


class BNBHandler(PlatformContractHandler):

    def __init__(self, provider: str = settings.CONTRACT_SETTINGS['BNB']['PROVIDER']):
        super().__init__(provider)
        self.contract = self.web3.eth.contract(
            address=settings.CONTRACT_SETTINGS['BNB']['PLATFORM_CONTRACT_ADDRESS'],
            abi=settings.CONTRACT_SETTINGS['BNB']['PLATFORM_CONTRACT_ABI']
        )


class ContractFactory:

    def __new__(cls, _type: str, *args, **kwargs):
        if _type == BlockChainType.POLYGON.value:
            return PolygonHandler()
        elif _type == BlockChainType.BNB.value:
            return BNBHandler()
        else:
            raise TypeError(f'Type `{_type}` is not supported.')
