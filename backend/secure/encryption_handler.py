from ctypes import *
import os
from django.conf import settings
from pathlib import Path


class GoString(Structure):
    _fields_ = [("p", c_char_p), ("n", c_longlong)]


class EncryptionHandler:

    def __init__(self):
        # self.eh = CDLL('D:\workspace\d-book\\backend\secure\libs\dbook_server.dll')
        self.eh = cdll.LoadLibrary(os.path.join(settings.BASE_DIR, 'secure/libs/homomorphic_encryption.so'))

    def check_file(self, file: str):
        abs_path = os.path.join(settings.ENCRYPTION_ROOT, file)
        # make dir
        _dir = abs_path.rsplit('/', 1)[0]
        os.makedirs(_dir, exist_ok=True)
        # create file
        # if os.path.exists(abs_path):
        #     os.remove(abs_path)
        f = Path(abs_path)
        f.touch(exist_ok=True)

    def to_go_string(self, file: str):
        return GoString(c_char_p(file.encode('utf-8')), c_longlong(len(file)))

    def generate_private_key(self, file: str):
        """
        :param file: str, file path
        :return:
        """
        print('Generate private key...')
        self.check_file(file)
        print(f'file -> {file}')
        func_gen_sk = self.eh.GenSK
        _file = self.to_go_string(file)
        func_gen_sk.argtypes = [GoString]
        func_gen_sk(_file)

    def generate_public_key(self, file: str, sk_file: str):
        """
        :param file: str, file path
        :param sk_file: str, private key file path
        :return:
        """
        print('Generate public key...')
        self.check_file(file)
        func_gen_pk = self.eh.GenPK
        _sk_file = self.to_go_string(sk_file)
        _file = self.to_go_string(file)
        func_gen_pk.argtypes = [GoString, GoString]
        func_gen_pk(_sk_file, _file)

    def generate_key_dict(self, file: str, sk_file: str):
        """
        :param file: str, file path
        :param sk_file: str, private key file path
        :return:
        """
        print('Generate key dict...')
        self.check_file(file)
        func_gen_dict = self.eh.GenDict
        _sk_file = self.to_go_string(sk_file)
        _file = self.to_go_string(file)
        func_gen_dict.argtypes = [GoString, GoString]
        func_gen_dict(_sk_file, _file)
