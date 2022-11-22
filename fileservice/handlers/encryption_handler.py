from ctypes import *
import os
import uuid
from pathlib import Path
from Crypto.Cipher import AES


class GoString(Structure):
    _fields_ = [("p", c_char_p), ("n", c_longlong)]


class EncryptionHandler:

    def encrypt(self, *args, **kwargs):
        raise NotImplementedError()

    def decrypt(self, *args, **kwargs):
        raise NotImplementedError()


class HomomorphicEncryptionHandler(EncryptionHandler):
    BASE_DIR = Path(__file__).resolve().parent.parent

    def __init__(self):
        self.he = cdll.LoadLibrary(os.path.join(self.BASE_DIR, 'libs/homomorphic_encryption.so'))

    def __check_file(self, path: str):
        # make dir
        _dir = path.rsplit('/', 1)[0]
        os.makedirs(_dir, exist_ok=True)
        # create file
        # if os.path.exists(abs_path):
        #     os.remove(abs_path)
        f = Path(path)
        f.touch(exist_ok=True)

    def check_key(self, file: str):
        abs_path = os.path.join(self.BASE_DIR, 'file', file)
        self.__check_file(abs_path)

    def check_img(self, file: str):
        abs_path = os.path.join(self.BASE_DIR, 'workspace', file)
        self.__check_file(abs_path)

    def get_watermark_img(self):
        return 'bwm16x16.png'

    def to_go_string(self, file: str):
        b_file = file.encode('utf-8')
        return GoString(c_char_p(b_file), c_longlong(len(b_file)))

    def generate_private_key(self, file: str):
        """
        :param file: str, file path
        :return:
        """
        print('Generate private key...')
        self.check_key(file)
        print(f'file -> {file}')
        func_gen_sk = self.he.GenSK
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
        self.check_key(file)
        func_gen_pk = self.he.GenPK
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
        self.check_key(file)
        func_gen_dict = self.he.GenDict
        _sk_file = self.to_go_string(sk_file)
        _file = self.to_go_string(file)
        func_gen_dict.argtypes = [GoString, GoString]
        func_gen_dict(_sk_file, _file)

    def encrypt(self, sk_file: str, org_img: str, enc_img: str):
        """
        Encrypt image
        :param sk_file: str, private key file
        :param org_img: str, original image file
        :param enc_img: str, encrypted image file
        :return: no
        """
        print(f'Encrypting images, sk file -> {sk_file}, org img -> {org_img}, enc img -> {enc_img}')
        self.check_img(enc_img)
        _sk_file = self.to_go_string(sk_file)
        _org_img = self.to_go_string(org_img)
        _enc_img = self.to_go_string(enc_img)
        func_encrypt_img = self.he.EncryptImage
        func_encrypt_img.argtypes = [GoString, GoString, GoString]
        func_encrypt_img(_sk_file, _org_img, _enc_img)

    def add_sign(self, sk_file: str, org_img: str):
        """
        Sign file
        :param sk_file: str, private key file
        :param org_img: str, original image file
        :return: no
        """
        print(f'Add sign, org img -> {org_img}')
        _sk_file = self.to_go_string(sk_file)
        _org_img = self.to_go_string(org_img)
        func_add_sign = self.he.AddSign
        func_add_sign.argtypes = [GoString, GoString]
        func_add_sign(_org_img, _sk_file)

    def add_bwm(self, org_img: str, enc_img: str):
        """
        add watermark
        :param org_img: str, original image file
        :param enc_img: str, encrypted image file
        :return: no
        """
        print(f"Add blind watermark, org img -> {org_img}, enc img -> {enc_img}")
        _org_img = self.to_go_string(org_img)
        _bwm_img = self.to_go_string(self.get_watermark_img())
        _enc_img = self.to_go_string(enc_img)
        func_add_bwm = self.he.AddBWM
        func_add_bwm.argtypes = [GoString, GoString, GoString]
        func_add_bwm(_org_img, _bwm_img, _enc_img)

    def decrypt(self, sk_file: str, enc_img: str, dec_img: str):
        """
        decrypt image
        :param sk_file: str, private key file
        :param enc_img: str, encrypted image file
        :param dec_img: str, decrypted image file
        :return: no
        """
        print(f"Decrypt image, sk file -> {sk_file}, enc file -> {enc_img}, dec file -> {dec_img}")
        _sk_file = self.to_go_string(sk_file)
        _enc_img = self.to_go_string(enc_img)
        _dec_img = self.to_go_string(dec_img)
        func_decrypt_img = self.he.DecryptImage
        func_decrypt_img.argtypes = [GoString, GoString, GoString]
        func_decrypt_img(_sk_file, _enc_img, _dec_img)

    def verify_sign(self, img_file: str, dict_file: str) -> bool:
        """
        Verify signature
        :param img_file: str, image file
        :param dict_file: str, key dict file
        :return: bool
        """
        print(f"Verify signature, img file -> {img_file}, dict file -> {dict_file}")
        _img_file = self.to_go_string(img_file)
        _dict_file = self.to_go_string(dict_file)
        func_verify_sign = self.he.VerifySign
        func_verify_sign.argtypes = [GoString, GoString]
        func_verify_sign.restype = c_bool
        return func_verify_sign(_img_file, _dict_file)

    def view_bwm(self, img_file: str, bwm_img: str):
        """
        View blind watermark
        :param img_file: str, image file
        :param bwm_img: str, watermark image file
        :return: no
        """
        print(f"View watermark, img file -> {img_file}, bwm img -> {bwm_img}")
        _img_file = self.to_go_string(img_file)
        _bwm_img = self.to_go_string(bwm_img)
        func_view_bwm = self.he.ViewBWM
        func_view_bwm.argtypes = [GoString, GoString]
        func_view_bwm(_img_file, _bwm_img)


class AESHandler(EncryptionHandler):
    chunk_size = 1024

    def encrypt(self, key: bytes, text: bytes) -> tuple:
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(text)
        return cipher.nonce, tag, ciphertext

    def decrypt(self, key: bytes, ciphertext: bytes, nonce: bytes, tag: bytes) -> bytes:
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        text = cipher.decrypt_and_verify(ciphertext, tag)
        return text

    def encrypt_file(self, key: bytes, file: str):
        cipher_file = f'{file}.bin'
        with open(cipher_file, 'wb') as f_out:
            with open(file, 'rb') as f_in:
                text = f_in.read(self.chunk_size)
                while text:
                    for item in self.encrypt(key, text):
                        f_out.write(item)
                    text = f_in.read(self.chunk_size)

        return cipher_file

    def decrypt_file(self, key: bytes, file: str):
        decrypted_file = f'{file}.pdf'
        with open(decrypted_file, 'wb') as f_out:
            with open(file, 'rb') as f_in:
                nonce, tag, ciphertext = [f_in.read(x) for x in (16, 16, self.chunk_size)]
                while nonce:
                    text = self.decrypt(key, ciphertext, nonce, tag)
                    f_out.write(text)
                    nonce, tag, ciphertext = [f_in.read(x) for x in (16, 16, self.chunk_size)]
        return decrypted_file
