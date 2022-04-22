from web3 import Web3
import json
from web3.middleware import geth_poa_middleware

admin_address = '0x41eA6aD88bbf4E22686386783e7817bB7E82c1ed'
platform_address = '0x4f2C793DB2163A7A081b984E6E8e2c504825668b'
seller_address = '0x46A26B330c0988a58aFF56e2a106F8256Ca89872'
publisher_address = '0xebE2F80dFc5Eb9b84693089BC483064dca6F40c6'
buyer_address = '0x2A5f210545521466A3d77D8ACf89ae026DB31eb1'
gasPrice = 0x02540be400
gasLimit = 0x7a1200

mumbai_usdc_contract_address = '0xB556b362EC02d2384F4645d7160562538fdf40c4'
mumbai_nft_contract_address = '0xa18C1feF1F76a554cD716096f39a051cf4F94523'
mumbai_platform_contract_address = '0x662E48096EA75f1F5CfF8cF286BAD19278368B6a'


class ContractHandler:
    ADMIN_ADDRESS = '0x41eA6aD88bbf4E22686386783e7817bB7E82c1ed'
    ADMIN_PRIVATE_KEY = '0xc03b0a988e2e18794f2f0e881d7ffcd340d583f63c1be078426ae09ddbdec9f5'
    PLATFORM_ADDRESS = '0x4f2C793DB2163A7A081b984E6E8e2c504825668b'

    def __init__(self, provider: str):
        self.w3 = Web3(Web3.HTTPProvider(provider))
        # self.w3.eth.default_account = self.ADMIN_ADDRESS
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        assert self.w3.isConnected(), 'Cannot connect to network'
        self.admin_account = self.w3.eth.account.from_key(self.ADMIN_PRIVATE_KEY)
        self.nft_contract = None
        self.platform_contract = None
        self.erc_contract = None

    def __get_contract(self, address, abi):
        return self.w3.eth.contract(address=address, abi=abi)

    def __check_nft_contract(self):
        assert self.nft_contract is not None, 'Please build nft fileservice firstly with set_nft_contract()'

    def __check_platform_contract(self):
        assert self.platform_contract is not None, 'Please build platform fileservice firstly with set_platform_contract()'

    def __check_erc_contract(self):
        assert self.erc_contract is not None, 'Please build erc fileservice firstly with set_erc_contract()'

    def set_nft_contract(self, address, abi):
        self.nft_contract = self.__get_contract(address, abi)
        return self

    def init_nft_contract(self):
        self.__check_nft_contract()
        self.__check_platform_contract()
        # todo need to connect to admin wallet
        nonce = self.w3.eth.get_transaction_count(self.ADMIN_ADDRESS)
        txn = self.nft_contract.functions.setPlatformAddress(self.platform_contract.address).buildTransaction(
            {'from': self.ADMIN_ADDRESS, 'nonce': nonce})
        self.transact_with_admin(txn)
        return self

    def set_platform_contract(self, address, abi):
        self.platform_contract = self.__get_contract(address, abi)
        return self

    def init_platform_contract(self):
        self.__check_platform_contract()
        # set platform wallet address for receiving platform fee
        # todo need to connect to admin wallet
        nonce = self.w3.eth.get_transaction_count(self.ADMIN_ADDRESS)
        txn = self.platform_contract.functions.setPlatformAddress(platform_address).buildTransaction(
            {'from': self.ADMIN_ADDRESS, 'nonce': nonce})
        self.transact_with_admin(txn)
        # set fee for platform
        nonce = self.w3.eth.get_transaction_count(self.ADMIN_ADDRESS)
        txn = self.platform_contract.functions.setFee(1000000).buildTransaction(
            {'from': self.ADMIN_ADDRESS, 'nonce': nonce})
        self.transact_with_admin(txn)
        # set platform ratio %%
        nonce = self.w3.eth.get_transaction_count(self.ADMIN_ADDRESS)
        txn = self.platform_contract.functions.setPlatformRatio(250).buildTransaction(
            {'from': self.ADMIN_ADDRESS, 'nonce': nonce})
        self.transact_with_admin(txn)
        return self

    def set_erc_contract(self, address, abi):
        self.erc_contract = self.__get_contract(address, abi)
        return self

    def transact_with_admin(self, transaction):
        signed_txn = self.admin_account.sign_transaction(transaction)
        txn_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        self.w3.eth.wait_for_transaction_receipt(txn_hash)
        return txn_hash

    def approve_publisher(self, publisher: str):
        try:
            # check address
            publisher = Web3.toChecksumAddress(publisher)
            # add auth for seller
            # todo need to connect to admin wallet, so this step should be finished by admin before issuing.
            nonce = self.w3.eth.get_transaction_count(self.ADMIN_ADDRESS)
            txn = self.platform_contract.functions.addAuth(publisher).buildTransaction(
                {'from': self.ADMIN_ADDRESS, 'nonce': nonce})
            txn_hash = self.transact_with_admin(txn)
            print(txn_hash)

            minters = self.platform_contract.functions.getIssueList().call()
            print('minters: ', minters)
            return True
        except Exception as e:
            print(e)
            return False

    def issue(self, publisher: str, publisher_ratio: int, seller: str, nft_id: int, price: int, amount: int,
              metadata: str):
        self.__check_platform_contract()
        self.__check_nft_contract()

        # seller account
        # 1, connect to seller wallet
        # 2, approve platform fileservice that could mint the NFT
        # 3, issue book
        # todo need to connect to seller wallet
        seller_account = self.w3.eth.account.from_key(
            '0xcb93f47f4ae6e2ee722517f3a2d3e7f55a5074f430c9860bcfe1d6d172492ed0')

        # check address
        publisher = Web3.toChecksumAddress(publisher)
        seller = Web3.toChecksumAddress(seller)

        # set approval
        nonce = self.w3.eth.get_transaction_count(seller)
        txn = self.nft_contract.functions.setApprovalForAll(self.platform_contract.address, True).buildTransaction(
            {'from': seller, 'nonce': nonce})
        signed_txn = seller_account.sign_transaction(txn)
        txn_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        self.w3.eth.wait_for_transaction_receipt(txn_hash)

        # issue book
        nonce = self.w3.eth.get_transaction_count(seller)
        txn = self.platform_contract.functions.issue(seller, nft_id, amount, metadata, price, publisher,
                                                     publisher_ratio).buildTransaction(
            {'from': seller, 'nonce': nonce})
        signed_txn = seller_account.sign_transaction(txn)
        txn_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        txn_receipt = self.w3.eth.wait_for_transaction_receipt(txn_hash)
        print(txn_receipt)
        return txn_receipt

    def trade(self, seller: str, buyer: str, nft_id: int, amount: int, value: int, metadata: str, fee: int = 0):
        self.__check_platform_contract()
        self.__check_erc_contract()

        # check address
        seller = Web3.toChecksumAddress(seller)
        buyer = Web3.toChecksumAddress(buyer)

        # buyer account
        # todo need to connect to buyer wallet
        buyer_account = self.w3.eth.account.from_key(
            '0x64cbfcd7052f3ce2e1160e73370fd4f5e8a087d749d687c2695a92e9a6fa6ed8')

        # approve allowance for buyer
        # 1, connect to buyer wallet
        # 2, approve allowance with erc fileservice
        # 3, buy NFT
        nonce = self.w3.eth.get_transaction_count(buyer)
        txn = self.erc_contract.functions.approve(self.platform_contract.address, 10000000000).buildTransaction(
            {'from': buyer, 'nonce': nonce})
        signed_txn = buyer_account.sign_transaction(txn)
        txn_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        self.w3.eth.wait_for_transaction_receipt(txn_hash)

        # trade
        nonce = self.w3.eth.get_transaction_count(buyer)
        txn = self.platform_contract.functions.trade(seller, buyer, nft_id, amount, metadata, value,
                                                     fee).buildTransaction(
            {'from': buyer, 'nonce': nonce})
        signed_txn = buyer_account.sign_transaction(txn)
        txn_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        txn_receipt = self.w3.eth.wait_for_transaction_receipt(txn_hash)
        print(txn_receipt)
        return txn_receipt

    def set_nft_price(self, nft_id: int, price: int):
        self.__check_platform_contract()
        nonce = self.w3.eth.get_transaction_count(self.ADMIN_ADDRESS)
        txn = self.platform_contract.functions.setNftPrice(nft_id, price).buildTransaction(
            {'from': self.ADMIN_ADDRESS, 'nonce': nonce})
        self.transact_with_admin(txn)


if __name__ == '__main__':
    usdc_address = '0xb43DCCBCb80e1e77dC94107568407AFf6F3879b2'
    usdc_abi = '''
    [
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "_name",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "_symbol",
          "type": "string"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        },
        {
          "internalType": "uint8",
          "name": "decimals",
          "type": "uint8"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "indexed": true,
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "indexed": false,
          "internalType": "uint256",
          "name": "value",
          "type": "uint256"
        }
      ],
      "name": "Approval",
      "type": "event"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "internalType": "address",
          "name": "from",
          "type": "address"
        },
        {
          "indexed": true,
          "internalType": "address",
          "name": "to",
          "type": "address"
        },
        {
          "indexed": false,
          "internalType": "uint256",
          "name": "value",
          "type": "uint256"
        }
      ],
      "name": "Transfer",
      "type": "event"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        }
      ],
      "name": "allowance",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "approve",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "account",
          "type": "address"
        }
      ],
      "name": "balanceOf",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "decimals",
      "outputs": [
        {
          "internalType": "uint8",
          "name": "",
          "type": "uint8"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "subtractedValue",
          "type": "uint256"
        }
      ],
      "name": "decreaseAllowance",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "addedValue",
          "type": "uint256"
        }
      ],
      "name": "increaseAllowance",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "name",
      "outputs": [
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "symbol",
      "outputs": [
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalSupply",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "recipient",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "transfer",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "sender",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "recipient",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "transferFrom",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ]
    '''
    nft_address = '0xb43DCCBCb80e1e77dC94107568407AFf6F3879b2'
    nft_abi = '''
    [{"inputs":[{"internalType":"string","name":"name","type":"string"},
    {"internalType":"string","name":"symbol","type":"string"},
    {"internalType":"string","name":"uri","type":"string"}],
    "stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"account","type":"address"},
    {"indexed":true,"internalType":"address","name":"operator","type":"address"},
    {"indexed":false,"internalType":"bool","name":"approved","type":"bool"}],
    "name":"ApprovalForAll","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},
    {"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],
    "name":"OwnershipTransferred","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"operator","type":"address"},
    {"indexed":true,"internalType":"address","name":"from","type":"address"},
    {"indexed":true,"internalType":"address","name":"to","type":"address"},
    {"indexed":false,"internalType":"uint256[]","name":"ids","type":"uint256[]"},
    {"indexed":false,"internalType":"uint256[]","name":"values","type":"uint256[]"}],
    "name":"TransferBatch","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"operator","type":"address"},
    {"indexed":true,"internalType":"address","name":"from","type":"address"},
    {"indexed":true,"internalType":"address","name":"to","type":"address"},
    {"indexed":false,"internalType":"uint256","name":"id","type":"uint256"},
    {"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"TransferSingle","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"value","type":"string"},
    {"indexed":true,"internalType":"uint256","name":"id","type":"uint256"}],"name":"URI","type":"event"},
    {"inputs":[{"internalType":"address","name":"account","type":"address"},
    {"internalType":"uint256","name":"id","type":"uint256"}],
    "name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
    "stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address[]","name":"accounts","type":"address[]"},
    {"internalType":"uint256[]","name":"ids","type":"uint256[]"}],
    "name":"balanceOfBatch","outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"}],
    "stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"},
    {"internalType":"address","name":"operator","type":"address"}],
    "name":"isApprovedForAll","outputs":[{"internalType":"bool","name":"","type":"bool"}],
    "stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},
    {"internalType":"uint256","name":"tokenId","type":"uint256"},
    {"internalType":"uint256","name":"amount","type":"uint256"},
    {"internalType":"bytes","name":"data","type":"bytes"}],
    "name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],
    "stateMutability":"view","type":"function"},{"inputs":[],"name":"owner",
    "outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"from","type":"address"},
    {"internalType":"address","name":"to","type":"address"},
    {"internalType":"uint256[]","name":"ids","type":"uint256[]"},
    {"internalType":"uint256[]","name":"amounts","type":"uint256[]"},
    {"internalType":"bytes","name":"data","type":"bytes"}],
    "name":"safeBatchTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"from","type":"address"},
    {"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"},
    {"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],
    "name":"safeTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"operator","type":"address"},
    {"internalType":"bool","name":"approved","type":"bool"}],
    "name":"setApprovalForAll","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"platformAddress","type":"address"}],
    "name":"setPlatformAddress","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],
    "name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],
    "stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol",
    "outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],
    "name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],
    "name":"uri","outputs":[{"internalType":"string","name":"","type":"string"}],
    "stateMutability":"view","type":"function"}]
    '''
    platform_contract_address = '0xdb998E9185A0ABC9fdA297501cf7aed1D0e76da5'
    platform_contract_abi = '''
    [{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"to","type":"address"},
    {"indexed":false,"internalType":"uint256","name":"nftId","type":"uint256"},
    {"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"},
    {"indexed":false,"internalType":"bytes","name":"data","type":"bytes"},
    {"indexed":false,"internalType":"uint256","name":"price","type":"uint256"},
    {"indexed":false,"internalType":"address","name":"publisherAddress","type":"address"},
    {"indexed":false,"internalType":"uint256","name":"publisherRatio","type":"uint256"}],"name":"Issue","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"seller","type":"address"},
    {"indexed":false,"internalType":"address","name":"receiver","type":"address"},
    {"indexed":false,"internalType":"uint256","name":"nftId","type":"uint256"},
    {"indexed":false,"internalType":"uint256","name":"nftAmount","type":"uint256"},
    {"indexed":false,"internalType":"bytes","name":"data","type":"bytes"},
    {"indexed":false,"internalType":"uint256","name":"tradeValue","type":"uint256"},
    {"indexed":false,"internalType":"uint256","name":"fee","type":"uint256"}],"name":"Trade","type":"event"},
    {"inputs":[{"internalType":"address","name":"token1155","type":"address"},
    {"internalType":"address","name":"token20","type":"address"},
    {"internalType":"string","name":"version","type":"string"}],
    "name":"__DBookPlatform_init","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"minter","type":"address"}],
    "name":"addAuth","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"minter","type":"address"}],
    "name":"delAuth","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"getFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
    "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getFrozen","outputs":[{"internalType":"bool","name":"","type":"bool"}],
    "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getIssueList","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],
    "stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"nftId","type":"uint256"}],
    "name":"getNftPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
    "stateMutability":"view","type":"function"},{"inputs":[],"name":"getPlatformAddress",
    "outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getPlatformRatio","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
    "stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"nftId","type":"uint256"}],
    "name":"getPublisherAddress","outputs":[{"internalType":"address","name":"","type":"address"}],
    "stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"nftId","type":"uint256"}],
    "name":"getPublisherRatio","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
    "stateMutability":"view","type":"function"},{"inputs":[],"name":"getVersion",
    "outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"to","type":"address"},
    {"internalType":"uint256","name":"nftId","type":"uint256"},
    {"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"},
    {"internalType":"uint256","name":"price","type":"uint256"},
    {"internalType":"address","name":"publisherAddress","type":"address"},
    {"internalType":"uint256","name":"publisherRatio","type":"uint256"}],
    "name":"issue","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"fee","type":"uint256"}],
    "name":"setFee","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"bool","name":"isFrozen","type":"bool"}],"name":"setFrozen","outputs":[],
    "stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"nftId","type":"uint256"},
    {"internalType":"uint256","name":"price","type":"uint256"}],
    "name":"setNftPrice","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"platformAddress","type":"address"}],
    "name":"setPlatformAddress","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"platformRatio","type":"uint256"}],
    "name":"setPlatformRatio","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"nftId","type":"uint256"},
    {"internalType":"address","name":"publishAddress","type":"address"}],
    "name":"setPublisherAddress","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"nftId","type":"uint256"},
    {"internalType":"uint256","name":"publishRatio","type":"uint256"}],"name":"setPublisherRatio","outputs":[],
    "stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"string","name":"version","type":"string"}],
    "name":"setVersion","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"seller","type":"address"},{"internalType":"address",
    "name":"receiver","type":"address"},{"internalType":"uint256","name":"nftId","type":"uint256"},
    {"internalType":"uint256","name":"nftAmount","type":"uint256"},{"internalType":"bytes",
    "name":"data","type":"bytes"},{"internalType":"uint256","name":"tradeValue","type":"uint256"},
    {"internalType":"uint256","name":"fee","type":"uint256"}],
    "name":"trade","outputs":[],"stateMutability":"nonpayable","type":"function"}]
    '''

    # connect to network
    contract_handler = ContractHandler('https://rpc-mumbai.matic.today')

    contract_handler.set_nft_contract(mumbai_nft_contract_address, json.loads(nft_abi)).set_platform_contract(
        mumbai_platform_contract_address, json.loads(platform_contract_abi)).set_erc_contract(
        mumbai_usdc_contract_address, json.loads(usdc_abi))
    # init fileservice
    # contract_handler.init_nft_contract().init_platform_contract()

    # issue book
    price = Web3.toWei(0.001, 'ether')
    metadata = Web3.toHex(
        text=json.dumps({'name': 'Harry Pot 2', 'description': 'Magic book', 'token': '0xfadf33333332saffsfd224'})
    )
    nft_id = 0x02
    # contract_handler.issue(publisher_address, 2000, seller_address, nft_id, price, 10, metadata)
    # contract_handler.set_nft_price(nft_id, 5000000)
    # buy book
    amount = 1
    value = 10000000
    contract_handler.trade(seller_address, buyer_address, nft_id, amount, value, metadata, 1000000)
