from utils.smart_contract_handler import PlatformContractHandler
from tests.base import config


def test_add_author():
    pch = PlatformContractHandler()

    addr = config['wallet_addr']

    res = pch.add_author(addr)

    assert res