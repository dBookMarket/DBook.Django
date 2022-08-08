import fitz
import os
import shutil
from io import BytesIO
from .nft_storage_handler import NFTStorageHandler
from .encryption_handler import EncryptionHandler
import zipfile
from pathlib import Path
import uuid
import math

# from PIL import Image


class FileHandler(object):
    BASE_DIR = Path(__file__).resolve().parent.parent
    TMP_ROOT = os.path.join(BASE_DIR, 'workspace')
    KEY_ROOT = os.path.join(BASE_DIR, 'file')

    @classmethod
    def compress(cls, path: str):
        zip_file_path = os.path.join(cls.TMP_ROOT, f'{uuid.uuid4().hex}.zip')
        zip_file = Path(zip_file_path)
        zip_file.touch(exist_ok=True)
        current_dir = os.getcwd()
        try:
            with zipfile.ZipFile(zip_file, 'w') as zf:
                if os.path.isdir(path):
                    # step into the directory
                    os.chdir(path)
                    # iterate current dir
                    for root, dirs, files in os.walk('.'):
                        for f in sorted(files):
                            f_path = os.path.join(root, f)
                            zf.write(f_path, compress_type=zipfile.ZIP_DEFLATED)
                else:
                    # step into the last directory
                    paths = path.rsplit('/')
                    os.chdir(paths[0])
                    # build zip
                    zf.write(paths[1], compress_type=zipfile.ZIP_DEFLATED)
        except Exception as e:
            print(f'Exception when calling FileHandler->compress: {e}')
            shutil.rmtree(zip_file_path)
            raise
        finally:
            # back to old directory
            os.chdir(current_dir)
        return zip_file_path

    @classmethod
    def decompress(cls, zip_file):
        path = os.path.join(cls.TMP_ROOT, f'{uuid.uuid4().hex}')
        os.makedirs(path, exist_ok=True)
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(path)
        return path

    @classmethod
    def remove(cls, path: str):
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            if os.path.exists(path):
                os.remove(path)


class PDFHandler(FileHandler):
    PAGES_PER_DIR = 50
    PRIVATE_KEY_DIR = 'private_keys'
    PUBLIC_KEY_DIR = 'public_keys'
    KEY_DICT_DIR = 'key_dicts'

    def __init__(self, file: [str, BytesIO] = None):
        if isinstance(file, str):
            self.pdf = fitz.open(file)
        elif isinstance(file, BytesIO):
            self.pdf = fitz.open(stream=file, filetype='pdf')
        else:
            self.pdf = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pdf:
            self.pdf.close()

    def get_pages(self):
        return self.pdf.page_count

    def get_file_name(self) -> str:
        return self.pdf.name.rsplit('/')[-1].rsplit('.')[0]

    def get_img_dirs(self) -> list:
        """
        将图片分批存入多个文件夹中，以免上传时超出大小限制(<=31GiB)
        :return:
        """
        img_dirs = []
        pages = self.get_pages()
        n_batches = math.ceil(pages / self.PAGES_PER_DIR)  # number of dirs
        file_name = self.get_file_name()
        if not file_name:
            file_name = uuid.uuid4().hex
        for i in range(n_batches):
            img_dir_path = os.path.join(self.TMP_ROOT, f"{file_name}-{i}")

            if not os.path.exists(img_dir_path):
                os.makedirs(img_dir_path)
            img_dirs.append(img_dir_path)
        return img_dirs

    def to_img(self, img_dirs: list):
        """
        1, 获取pdf，将pdf转换为image，image存储的文件夹为pdf文件名，每一张image的命名为页码
        :return: self
        """
        # 图片缩放 {x*y} 倍
        zoom = {'x': 2.0, 'y': 2.0}
        try:
            matrix = fitz.Matrix(zoom['x'], zoom['y']).prerotate(0)
            n_digits = len(str(self.get_pages()))
            for i, page in enumerate(self.pdf):
                # todo if the page already is an image?
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                # 需要使用多位数做页码，不然后期排序会出现问题
                current_page = str(i + 1)
                p_num = '0' * (n_digits - len(current_page)) + current_page
                img_path = os.path.join(img_dirs[i // self.PAGES_PER_DIR], f'page-{p_num}.png')
                pixmap.pil_save(img_path, format='png', optimize=True)
                # # resize image 1024*1024
                # img = Image.open(img_path)
                # img = img.resize((1024, 1024), Image.ANTIALIAS)
                # img.save(img_path)
                print(f'dir {img_dirs[i // self.PAGES_PER_DIR]}, page {p_num}, '
                      f'image size: {pixmap.w}*{pixmap.h}*{pixmap.n}/8')
        except Exception as e:
            print(f'Exception when calling PDFHandler->to_img: {e}')
            raise

        return self

    def encrypt_img(self, sk_file: str, img_dirs: list):
        """
        调用加密接口对图片进行加密，加密完后存储到filestorage
        :param sk_file: str, 私钥文件
        :param img_dirs: list, 原图片文件目录
        :return: self
        """
        print("Encrypting images...")
        enc_handler = EncryptionHandler()
        for img_dir in img_dirs:
            print(f"Image directory -> {img_dir}")
            dir_name = img_dir.rsplit('/', 1)[-1]
            for f in os.listdir(img_dir):
                org_img = os.path.join(dir_name, f)
                # add blind watermark
                enc_handler.add_bwm(org_img, org_img)
                # add signature
                enc_handler.add_sign(sk_file, org_img)
                # encrypt image
                enc_img = f"{org_img}.sse"
                enc_handler.encrypt_img(sk_file, org_img, enc_img)
                # remove original image
                self.remove(os.path.join(img_dir, f))
        return self

    def decrypt_img(self, sk_file: str, img_dirs: list):
        """
        调用解密接口对图片进行解密
        :param sk_file: str, private key file
        :param img_dirs: list, encrypted images directory list
        :return: str
        """
        print('Decrypting images...')
        enc_handler = EncryptionHandler()
        for img_dir in img_dirs:
            print(f"Image directory -> {img_dir}")
            dir_name = img_dir.rsplit('/', 1)[-1]
            for f in os.listdir(img_dir):
                enc_img = os.path.join(dir_name, f)
                dec_img = enc_img.rstrip('.sse')
                enc_handler.decrypt_img(sk_file, enc_img, dec_img)
        return self

    def generate_keys(self):
        """
        generate private/public keys and key dict file
        :return: tuple, (private key file, public key file, key dict file)
        """
        print(f'Generating keys...')
        base_name = uuid.uuid4().hex
        sk_file = os.path.join(self.PRIVATE_KEY_DIR, f'{base_name}.stk')
        pk_file = os.path.join(self.PUBLIC_KEY_DIR, f'{base_name}.pck')
        dict_file = os.path.join(self.KEY_DICT_DIR, f'{base_name}.dict')
        enc_handler = EncryptionHandler()
        enc_handler.generate_private_key(sk_file)
        enc_handler.generate_public_key(pk_file, sk_file)
        enc_handler.generate_key_dict(dict_file, sk_file)
        return sk_file, pk_file, dict_file

    def upload(self) -> dict:
        """
        convert pdf to images with encryption, and store these images into nft.storage
        :return: dict, format:
                    {
                        cid: 'aa',
                        nft_url: 'https://aa.xxx',
                        n_pages: 12
                    }
        """
        print('Uploading files...')
        print('Step 0, generate keys')
        sk_file, pk_file, dict_file = self.generate_keys()
        print('Step 1, convert pdf to images')
        img_dirs = self.get_img_dirs()
        self.to_img(img_dirs)
        print('Step 2, encrypt images')
        self.encrypt_img(sk_file, img_dirs)
        # test decryption
        # self.decrypt_img(sk_file, img_dirs)
        try:
            print('Step 3, upload images to nft.storage')
            # store compressed file into nft.storage
            cids = [NFTStorageHandler().bulk_upload(img_dir) for img_dir in img_dirs]
            return {'cids': cids, 'n_pages': self.get_pages(),
                    'private_key': sk_file, 'public_key': pk_file, 'key_dict': dict_file}
        except Exception as e:
            # todo tell server the job status
            #  status 524 timeout
            #  status 413 payload too large
            #  status 502 bad gateway
            print(f'Exception when calling PDFHandler->upload: {e}')
            print(f'Remove key files...')
            self.remove(os.path.join(self.KEY_ROOT, sk_file))
            self.remove(os.path.join(self.KEY_ROOT, pk_file))
            self.remove(os.path.join(self.KEY_ROOT, dict_file))
            raise
        finally:
            # delete temporary files
            print('Step 4, remove images')
            for img_dir in img_dirs:
                self.remove(img_dir)
            print('Upload finished.')

    @classmethod
    def _get_file_urls(cls, cid: str) -> list:
        """
        get files from nft.storage
        :param cid: nft cid
        :return: list of str, format:
                    [
                        'https://{cid}.ipfs.nftstorage.link/page-001.png',
                        'https://{cid}.ipfs.nftstorage.link/page-002.png',
                        ...
                        'https://{cid}.ipfs.nftstorage.link/page-200.png'
                    ]
        """
        # 1, get files according to cid
        data = NFTStorageHandler().retrieve(cid)
        # sort urls to ordering pages
        urls = sorted([NFTStorageHandler().get_file_url(cid, file['name']) for file in data['files']])
        return urls

    def get_file_urls(self, cids: list) -> list:
        urls = []
        for cid in cids:
            urls.extend(self._get_file_urls(cid))
        return urls
