from web3 import Web3
from web3.middleware import geth_poa_middleware
from django.conf import settings
from utils.enums import BlockChainType, TransactionStatus
import logging

logger = logging.getLogger(__name__)


class TransactionFailure(Exception):
    pass


class PlatformContractHandler(object):
    ADMIN_KEY = settings.CONTRACT_SETTINGS['ADMIN_KEY']
    PLATFORM_KEY = settings.CONTRACT_SETTINGS['PLATFORM_KEY']
    PRECISION = 1_000_000

    def __init__(self, provider: str = settings.CONTRACT_SETTINGS.get('HTTP_PROVIDER')):
        self.web3 = Web3(Web3.HTTPProvider(provider))
        # Unfortunately, it does deviate from the yellow paper specification,
        # which constrains the extraData field in each block to a maximum of 32-bytes.
        # Geth’s PoA uses more than 32 bytes, so this middleware modifies the block data a bit before returning it.
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.admin_account = self.web3.eth.account.from_key(self.ADMIN_KEY)
        self.platform_account = self.web3.eth.account.from_key(self.PLATFORM_KEY)

        self.contract = None
        self.usdc_contract = None

    def to_usdc(self, amount: float) -> int:
        return int(amount * self.PRECISION)

    def to_percent_percent(self, ratio: float) -> int:
        """
        % -> %%
        """
        return int(ratio * 100)

    def get_gas_price(self):
        """
        BNB needs a gas price to send a transaction
        2 gwei -> 2*10^9 wei
        """
        # return Web3.toWei(2, 'gwei')
        return self.web3.eth.gas_price

    def build_transaction_params(self, kwargs: dict) -> dict:
        return kwargs

    def add_author(self, account_addr: str) -> bool:
        """
        Give the user issue permission from contract.
        """
        try:
            # check account address
            account_addr = Web3.toChecksumAddress(account_addr)

            logger.error(f'admin address -> {self.admin_account.address}')
            nonce = self.web3.eth.get_transaction_count(self.admin_account.address)
            transaction = self.contract.functions.addAuth(account_addr).buildTransaction(
                self.build_transaction_params({'from': self.admin_account.address, 'nonce': nonce})
            )
            signed_txn = self.admin_account.sign_transaction(transaction)
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        except Exception as e:
            logger.error(f'Exception when calling add_author -> {e}')
            return False
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return bool(receipt['status'] == 1)

    def approve_usdc_to_platform(self, amount: int, retry: int = 3):
        """
        Approve the platform contract amount of usdc to transfer.

        :param amount: int, the number of usdc
        :param retry: int, retry the transaction, default 3.
        """
        nonce = self.web3.eth.get_transaction_count(self.platform_account.address)
        transaction = self.usdc_contract.functions.approve(self.contract.address, amount).buildTransaction(
            self.build_transaction_params({'from': self.platform_account.address, 'nonce': nonce})
        )
        signed_txn = self.platform_account.sign_transaction(transaction)
        txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        # get result
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        if receipt['status'] != 1:
            if retry > 0:
                logger.info(f'{4 - retry}: retry to approve usdc to platform contract from platform wallet.')
                self.approve_usdc_to_platform(amount, retry - 1)
            else:
                raise TransactionFailure('Failed to approve usdc to platform contract by platform wallet.')

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
        logger.info(f'platform address->{self.platform_account.address}')
        # check address
        seller = Web3.toChecksumAddress(seller)
        buyer = Web3.toChecksumAddress(buyer)

        # set approve
        self.approve_usdc_to_platform(self.to_usdc(payment))

        # send transaction
        nonce = self.web3.eth.get_transaction_count(self.platform_account.address)
        transaction = self.contract.functions.runFirstTrade(seller, self.to_usdc(payment), mint_amount,
                                                            buyer, token_id, amount, '0x01').buildTransaction(
            self.build_transaction_params({'from': self.platform_account.address, 'nonce': nonce})
        )
        signed_txn = self.platform_account.sign_transaction(transaction)
        txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        # get result
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        status = TransactionStatus.SUCCESS.value if receipt['status'] == 1 else TransactionStatus.FAILURE.value

        return {
            'hash': txn_hash.hex(),
            'status': status
        }

    def money_back(self, to: str, amount: float) -> bool:
        """
        if the transaction is failed, pay back to the buyer.
        :param to: str, buyer address
        :param amount: float, payment for the NFT

        :return: bool
        """
        # check address
        to = Web3.toChecksumAddress(to)

        # send transaction
        txn_hash = self.web3.eth.send_transaction(self.build_transaction_params({
            'from': self.admin_account.address,
            'to': to,
            'value': self.to_usdc(amount)
        }))
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

    def set_token_price(self, token_id: int, price: float) -> tuple:
        try:
            nonce = self.web3.eth.get_transaction_count(self.admin_account.address)
            txn = self.contract.functions.setNftPrice(token_id, self.to_usdc(price)).buildTransaction(
                self.build_transaction_params({'from': self.admin_account.address, 'nonce': nonce})
            )
            signed_txn = self.admin_account.sign_transaction(txn)
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        except Exception as e:
            logger.error(f'Exception when setting nft price->{e}')
            return '', False
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return txn_hash.hex(), receipt['status'] == 1

    def set_token_author(self, token_id: int, author: str) -> bool:
        try:
            author = Web3.toChecksumAddress(author)

            nonce = self.web3.eth.get_transaction_count(self.admin_account.address)
            txn = self.contract.functions.setPublisherAddress(token_id, author).buildTransaction(
                self.build_transaction_params({'from': self.admin_account.address, 'nonce': nonce})
            )
            signed_txn = self.admin_account.sign_transaction(txn)
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        except Exception as e:
            logger.error(f'Exception when setting nft price->{e}')
            return False
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return receipt['status'] == 1

    def set_token_royalty(self, token_id: int, royalty: float) -> bool:
        try:
            nonce = self.web3.eth.get_transaction_count(self.admin_account.address)
            txn = self.contract.functions.setPublisherRatio(token_id,
                                                            self.to_percent_percent(royalty)).buildTransaction(
                self.build_transaction_params({'from': self.admin_account.address, 'nonce': nonce})
            )
            signed_txn = self.admin_account.sign_transaction(txn)
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        except Exception as e:
            logger.error(f'Exception when setting nft price->{e}')
            return False
        receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return receipt['status'] == 1

    def burn(self, owner: str, token_id: int, amount: int, retry: int = 3) -> tuple:
        try:
            owner = Web3.toChecksumAddress(owner)
            # success = self.add_author(self.admin_account.address)
            # if not success:
            #     raise RuntimeError(f'Cannot add auth for {owner}')

            nonce = self.web3.eth.get_transaction_count(self.admin_account.address)
            txn = self.contract.functions.burn(owner, token_id, amount).buildTransaction(
                self.build_transaction_params({'from': self.admin_account.address, 'nonce': nonce})
            )
            signed_txn = self.admin_account.sign_transaction(txn)
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)

            if receipt['status'] == 1:
                return txn_hash.hex(), True
            else:
                if retry > 0:
                    logger.info(f'{4 - retry}: retry to burn {amount} nft({token_id}) of {owner}')
                    self.burn(owner, token_id, amount, retry - 1)
                else:
                    return '', False
        except Exception as e:
            logger.error(f'Exception when burning nft->{e}')
            return '', False


class PolygonHandler(PlatformContractHandler):

    def __init__(self, provider: str = settings.CONTRACT_SETTINGS['POLYGON']['PROVIDER']):
        super().__init__(provider)
        self.contract = self.web3.eth.contract(
            address=settings.CONTRACT_SETTINGS['POLYGON']['PLATFORM_CONTRACT_ADDRESS'],
            abi=settings.CONTRACT_SETTINGS['POLYGON']['PLATFORM_CONTRACT_ABI']
        )
        self.usdc_contract = self.web3.eth.contract(
            address=settings.CONTRACT_SETTINGS['POLYGON']['USDC_CONTRACT_ADDRESS'],
            abi=settings.CONTRACT_SETTINGS['POLYGON']['USDC_CONTRACT_ABI']
        )


class BNBHandler(PlatformContractHandler):

    def __init__(self, provider: str = settings.CONTRACT_SETTINGS['BNB']['PROVIDER']):
        super().__init__(provider)
        self.contract = self.web3.eth.contract(
            address=settings.CONTRACT_SETTINGS['BNB']['PLATFORM_CONTRACT_ADDRESS'],
            abi=settings.CONTRACT_SETTINGS['BNB']['PLATFORM_CONTRACT_ABI']
        )
        self.usdc_contract = self.web3.eth.contract(
            address=settings.CONTRACT_SETTINGS['BNB']['USDC_CONTRACT_ADDRESS'],
            abi=settings.CONTRACT_SETTINGS['BNB']['USDC_CONTRACT_ABI']
        )

    def build_transaction_params(self, kwargs: dict) -> dict:
        _params = super().build_transaction_params(kwargs)
        _params['gasPrice'] = self.get_gas_price()
        return _params


class FilecoinHandler(PlatformContractHandler):

    def __init__(self, provider: str = settings.CONTRACT_SETTINGS['FILECOIN']['PROVIDER']):
        super().__init__(provider)
        self.contract = self.web3.eth.contract(
            address=settings.CONTRACT_SETTINGS['FILECOIN']['PLATFORM_CONTRACT_ADDRESS'],
            abi=settings.CONTRACT_SETTINGS['FILECOIN']['PLATFORM_CONTRACT_ABI']
        )
        self.usdc_contract = self.web3.eth.contract(
            address=settings.CONTRACT_SETTINGS['FILECOIN']['USDC_CONTRACT_ADDRESS'],
            abi=settings.CONTRACT_SETTINGS['FILECOIN']['USDC_CONTRACT_ABI']
        )

    def build_transaction_params(self, kwargs: dict) -> dict:
        _params = super().build_transaction_params(kwargs)
        _params['gasPrice'] = self.get_gas_price()
        _params['maxFeePerGas'] = Web3.toWei(3, 'gwei')
        _params['maxPriorityFeePerGas'] = Web3.toWei(2, 'gwei')
        return _params


class ContractFactory:

    def __new__(cls, _type: str, *args, **kwargs):
        if _type == BlockChainType.POLYGON.value:
            return PolygonHandler()
        elif _type == BlockChainType.BNB.value:
            return BNBHandler()
        elif _type == BlockChainType.FILECOIN.value:
            return FilecoinHandler()
        else:
            raise TypeError(f'Type `{_type}` is not supported.')
