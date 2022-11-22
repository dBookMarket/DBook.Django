from handlers.pdf_handler import PDFHandler
import os
import pytest
from pathlib import Path
from unittest.mock import patch, Mock


parent_path = Path(__file__).resolve().parent.parent
pdf_handler = PDFHandler(os.path.join(parent_path, 'files/test.pdf'))


def test_get_pages():
    pages = pdf_handler.get_pages()
    assert pages == 4


def test_get_file_name():
    f_name = pdf_handler.get_file_name()
    assert f_name == 'test'


def test_get_img_dirs():
    dirs = pdf_handler.get_img_dirs()
    assert len(dirs) == 1
    assert dirs[0].find('test-0') != -1
    assert dirs[0] == os.path.join(pdf_handler.TMP_ROOT, 'test-0')


def test_to_img():
    dirs = pdf_handler.get_img_dirs()

    pdf_handler.to_img(dirs)

    for root, dirs, files in os.walk(dirs[0]):
        for i, f in enumerate(sorted(files)):
            assert f'page-{i + 1}.png' == f


@patch('handlers.pdf_handler.EncryptionHandler')
def test_generate_keys(mock_eh):
    sk_file, pk_file, key_dict = pdf_handler.generate_keys()

    assert sk_file.find(pdf_handler.PRIVATE_KEY_DIR) != -1
    assert pk_file.find(pdf_handler.PUBLIC_KEY_DIR) != -1
    assert key_dict.find(pdf_handler.KEY_DICT_DIR) != -1


@patch('handlers.pdf_handler.EncryptionHandler')
def test_encrypt_img(mock_eh):
    img_dirs = [os.path.join(pdf_handler.TMP_ROOT, 'test-0')]
    pdf_handler.encrypt('xxx.stk', img_dirs)


@patch('handlers.pdf_handler.NFTStorageHandler')
@patch('handlers.pdf_handler.EncryptionHandler')
def test_upload(mock_eh, mock_nsh):
    pdf_handler.generate_keys = Mock()
    pdf_handler.get_img_dirs = Mock()

    pdf_handler.to_img = Mock()
    pdf_handler.encrypt = Mock()

    pdf_handler.remove = Mock()

    mock_nsh.return_value.bulk_upload.return_value = 'xxx'

    pdf_handler.get_img_dirs.return_value = ['abc', 'ccc']
    pdf_handler.generate_keys.return_value = ('aaa.stk', 'aaa.pck', 'aaa.dict')

    res = pdf_handler.upload()
    assert res['cids'] == ['xxx', 'xxx']
    assert res['n_pages'] == 4
    assert res['private_key'] == 'aaa.stk'
    assert res['public_key'] == 'aaa.pck'
    assert res['key_dict'] == 'aaa.dict'

    # raise exception
    mock_nsh.return_value.bulk_upload.side_effect = Exception()
    with pytest.raises(Exception):
        pdf_handler.upload()


def test_remove():
    pdf_handler.remove(PDFHandler.KEY_ROOT)
    assert not os.path.exists(PDFHandler.KEY_ROOT)

    # pdf_handler.get_img_dirs()
    # img_dir = os.path.join(PDFHandler.TMP_ROOT, 'test-0')
    # pdf_handler.remove(img_dir)
    # assert (not os.path.exists(img_dir))


@patch('handlers.pdf_handler.NFTStorageHandler')
def test_get_file_urls(mock_nsh):
    mock_nsh.return_value.retrieve.return_value = {'files': [{'name': 'a-0'}, {'name': 'a-2'}, {'name': 'a-1'}]}
    mock_nsh.return_value.get_file_url.return_value = 'a-0.xxx.com'

    urls = PDFHandler._get_file_urls('abc')
    assert len(urls) == 3
    assert urls[0] == 'a-0.xxx.com'
    assert urls[1] == 'a-0.xxx.com'
    assert urls[2] == 'a-0.xxx.com'
