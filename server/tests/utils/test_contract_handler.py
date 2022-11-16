from utils.smart_contract_handler import PlatformContractHandler
from tests.base import config
from unittest.mock import patch


@patch('utils.smart_contract_handler.Web3')
def test_add_author(mock_w3):
    pch = PlatformContractHandler()

    addr = config['wallet_addr']

    mock_w3.return_value.eth.get_transaction_receipt.return_value = {'status': 1}
    res = pch.add_author(addr)
    assert res

    mock_w3.return_value.eth.get_transaction_receipt.return_value = {'status': 0}
    res = pch.add_author(addr)
    assert not res