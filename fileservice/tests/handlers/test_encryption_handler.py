import os
from pathlib import Path
from handlers.encryption_handler import AESHandler
from Crypto.Random import get_random_bytes

parent_path = Path(__file__).resolve().parent.parent


def test_aes_encrypt():
    text = b'abcdef'
    aes_handler = AESHandler()
    key = get_random_bytes(16)
    nonce, tag, ciphertext = aes_handler.encrypt(key, text)
    assert len(ciphertext) == len(text)

    decrypted_text = aes_handler.decrypt(key, ciphertext, nonce, tag)
    assert decrypted_text == text


def test_aes_encrypt_file():
    file = os.path.join(parent_path, 'files/test.pdf')
    aes_handler = AESHandler()
    key = get_random_bytes(32)
    encrypted_file = aes_handler.encrypt_file(key, file)
    assert os.path.exists(encrypted_file)

    decrypted_file = aes_handler.decrypt_file(key, encrypted_file)
    assert os.path.exists(decrypted_file)

    os.remove(encrypted_file)
    os.remove(decrypted_file)
