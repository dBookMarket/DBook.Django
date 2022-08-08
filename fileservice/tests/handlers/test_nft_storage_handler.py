from handlers.nft_storage_handler import NFTStorageHandler
from unittest.mock import patch
# import nft_storage
import pytest
import os
from pathlib import Path

parent_path = Path(__file__).resolve().parent.parent


@patch('handlers.nft_storage_handler.nft_storage_api')
@patch('handlers.nft_storage_handler.nft_storage')
def test_store(mock_ns, mock_nsa):
    file = os.path.join(parent_path, 'files/test.pdf')
    nft_handler = NFTStorageHandler()
    mock_nsa.NFTStorageAPI.return_value.store.return_value = {'ok': True, 'value': {'cid': 'abc'}}

    res = nft_handler.store(file)

    assert res == 'abc'

    # return not ok
    mock_nsa.NFTStorageAPI.return_value.store.return_value = {'ok': False}
    with pytest.raises(RuntimeError):
        nft_handler.store(file)

    # raise exception
    # mock_nsa.NFTStorageAPI.return_value.store.side_effect = nft_storage.APIException()
    # with pytest.raises(nft_storage.APIException):
    #     nft_handler.store(file)


@patch('handlers.nft_storage_handler.MultipartEncoder')
@patch('handlers.nft_storage_handler.requests')
def test_bulk_upload(mock_reqs, mock_me):
    dir = os.path.join(parent_path, 'files')
    nft_handler = NFTStorageHandler()

    # not directory
    with pytest.raises(ValueError):
        nft_handler.bulk_upload('abc.txt')

    mock_reqs.post.return_value.json.return_value = {'ok': True, 'value': {'cid': 'abc'}}

    res = nft_handler.bulk_upload(dir)
    assert res == 'abc'

    # not ok
    mock_reqs.post.return_value.json.return_value = {'ok': False, 'error': {'message': 'errno 524xxxx'}}
    with pytest.raises(RuntimeError):
        nft_handler.bulk_upload(dir, 2)

    # raise exception when post
    mock_reqs.post.side_effect = ValueError('aaa')
    with pytest.raises(Exception):
        nft_handler.bulk_upload(dir)


@patch('handlers.nft_storage_handler.nft_storage_api')
@patch('handlers.nft_storage_handler.nft_storage')
def test_check(mock_ns, mock_nsa):
    cid = 'abc'
    nft_handler = NFTStorageHandler()

    mock_nsa.NFTStorageAPI.return_value.check.return_value = {'ok': True, 'value': 'xxx'}
    res = nft_handler.check(cid)
    assert res == 'xxx'

    # not ok
    mock_nsa.NFTStorageAPI.return_value.check.return_value = {'ok': False}
    with pytest.raises(RuntimeError):
        nft_handler.check(cid)

    # raise exception
    # todo TypeError: catching classes that do not inherit from BaseException is not allowed
    # mock_nsa.NFTStorageAPI.return_value.check.side_effect = nft_storage.APIException()
    # with pytest.raises(nft_storage.APIException):
    #     nft_handler.check(cid)


@patch('handlers.nft_storage_handler.nft_storage_api')
@patch('handlers.nft_storage_handler.nft_storage')
def test_delete(mock_ns, mock_nsa):
    cid = 'abc'
    nft_handler = NFTStorageHandler()

    mock_nsa.NFTStorageAPI.return_value.delete.return_value = {'ok': True}
    nft_handler.delete(cid)

    # not ok
    mock_nsa.NFTStorageAPI.return_value.delete.return_value = {'ok': False}
    with pytest.raises(RuntimeError):
        nft_handler.delete(cid)

    # raise exception
    # mock_nsa.NFTStorageAPI.return_value.delete.side_effect = nft_storage.APIException()
    # with pytest.raises(nft_storage.APIException):
    #     nft_handler.delete(cid)


@patch('handlers.nft_storage_handler.requests')
def test_retrieve(mock_reqs):
    cid = 'abc'
    nft_handler = NFTStorageHandler()

    mock_reqs.get.return_value.json.return_value = {'ok': True, 'value': 'xxx'}
    res = nft_handler.retrieve(cid)
    assert res == 'xxx'

    # not ok
    mock_reqs.get.return_value.json.return_value = {'ok': False, 'error': {'message': 'error'}}
    with pytest.raises(RuntimeError):
        nft_handler.retrieve(cid)

    # raise exception
    mock_reqs.get.side_effect = Exception()
    with pytest.raises(Exception):
        nft_handler.retrieve(cid)
