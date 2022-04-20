import fitz
import os
import shutil
from io import BytesIO
from books.nft_storage_handler import NFTStorageHandler
import zipfile
from django.conf import settings
from pathlib import Path
import uuid
import glob
import requests


class FileHandler:

    @classmethod
    def compress(cls, path: str):
        zip_file_path = os.path.join(settings.MEDIA_ROOT, f'{uuid.uuid4().hex}.zip')
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
        path = os.path.join(settings.TEMPORARY_ROOT, f'{uuid.uuid4().hex}')
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

    def to_img(self) -> str:
        """
        1, 获取pdf，将pdf转换为image，image存储的文件夹为pdf文件名，每一张image的命名为页码
        :return
            images directory path
        """
        zoom = {'x': 3.0, 'y': 3.0}
        # fragments = []
        try:
            file_name = self.get_file_name()
            if not file_name:
                file_name = uuid.uuid4().hex
            img_dir_path = os.path.join(settings.TEMPORARY_ROOT, file_name)

            if not os.path.exists(img_dir_path):
                os.makedirs(img_dir_path)

            matrix = fitz.Matrix(zoom['x'], zoom['y']).prerotate(0)
            n_digits = len(str(self.get_pages()))
            for i, page in enumerate(self.pdf):
                # todo if the page already is an image?
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                # todo 需要使用多位数做页码，不然后期排序会出现问题
                current_page = str(i + 1)
                p_num = '0' * (n_digits - len(current_page)) + current_page
                img_path = os.path.join(img_dir_path, f'page-{p_num}.jpg')
                pixmap.pil_save(img_path, optimize=True)
                # TODO 对图片进行加密
                # 存储到filestorage
                # cid = self.store_img(img_file_path)
                # 存储url
                # fragments.append({
                #     'file_url': f'{self.PREFIX}/{cid}',
                #     'token': cid,
                #     'page': i + 1
                # })
            # 销毁本地文件
            # self.remove(img_dir_path)
            return img_dir_path
        except Exception as e:
            print(f'Exception when calling PDFHandler->to_img: {e}')
            raise

    def encrypt_img(self, file_path: str):
        """
        调用加密接口对图片进行加密，加密完后存储到filestorage
        :param file_path:
        :return:
        """
        raise NotImplementedError

    def decrypt_img(self, file):
        """
        调用解密接口对图片进行解密，解密后的文件拼接成临时的pdf文件
        :param file:
        :return: str
        """
        raise NotImplementedError

    def save_img(self) -> str:
        """
        convert pdf to images, and store these images into nft.storage
        :return: str, nft token
        """
        img_dir_path = self.to_img()
        # compress images
        # zip_file_path = self.compress(img_dir_path)
        # store compressed file into nft.storage
        cid = NFTStorageHandler().bulk_store(img_dir_path)
        # delete temporary files
        self.remove(img_dir_path)
        # self.remove(zip_file_path)
        return cid

    # def download_by_url(self, url: str, path=None, chunk_size=128) -> str:
    #     print(f'Downloading zip file from {url}...')
    #     if path is None:
    #         file_name = f'{uuid.uuid4().hex}.zip'
    #         path = os.path.join(settings.TEMPORARY_ROOT, file_name)
    #     try:
    #         res = requests.get(url, stream=True, verify=False)
    #         with open(path, 'wb+') as file:
    #             for chunk in res.iter_content(chunk_size=chunk_size):
    #                 file.write(chunk)
    #         res.close()  # close connection
    #     except Exception as e:
    #         print(f'Exception when calling PDFHandler->download_by_url: {e}')
    #         self.remove(path)
    #         raise
    #     return path

    def download_images(self, urls: list, path=None, chunk_size=128) -> str:
        """
        :param urls: list of image url
        :param path: the dir which images will be saved in
        :param chunk_size: int
        :return: file dir path
        """
        if path is None:
            dir_name = f'{uuid.uuid4().hex}'
            path = os.path.join(settings.TEMPORARY_ROOT, dir_name)
            os.makedirs(path)
        if not os.path.isdir(path):
            raise ValueError('The value of path must be a directory path')
        try:
            n_digits = len(str(len(urls)))
            for idx, url in enumerate(urls):
                # InsecureRequestWarning: Unverified HTTPS request is being made to host
                res = requests.get(url, stream=True)
                current_page = str(idx + 1)
                p_num = '0' * (n_digits - len(current_page)) + current_page
                with open(os.path.join(path, f'page-{p_num}.jpg'), 'wb+') as f:
                    for chunk in res.iter_content(chunk_size=chunk_size):
                        f.write(chunk)
                res.close()
        except Exception as e:
            print(f'Exception when calling PDFHandler->download_images: {e}')
            self.remove(path)
            raise
        return path

    def to_pdf(self, img_dir) -> str:
        print(f'Converting images to pdf...')
        pdf_name = f'{uuid.uuid4().hex}.pdf'
        pdf_path = os.path.join(settings.TEMPORARY_ROOT, pdf_name)
        pdf_file = Path(pdf_path)
        pdf_file.touch(exist_ok=True)
        # create a new pdf
        pdf_doc = fitz.open()
        try:
            for img in sorted(glob.glob(os.path.join(img_dir, '*'))):
                # todo 解密图片
                # insert
                img_doc = fitz.open(img)
                pdf_bytes = img_doc.convert_to_pdf()
                img_pdf = fitz.open('pdf', pdf_bytes)
                pdf_doc.insert_pdf(img_pdf)
            pdf_doc.ez_save(pdf_file)
        except Exception as e:
            print(f'Exception when calling PDFHandler->save_pdf: {e}')
            raise
        finally:
            # delete images
            self.remove(img_dir)
            # close pdf doc
            pdf_doc.close()
        return f'{settings.TEMPORARY_DIR}/{pdf_name}'

    # def to_pdf_with_zip(self, zip_file) -> Path:
    #     """
    #     降解密后的image拼接成pdf，存储到media/tmp中
    #     :param zip_file: str or file-like object, the compressed file
    #     :return: str, pdf file
    #     """
    #     print(f'Converting images to pdf with zip file: {zip_file}')
    #     pdf_name = f'{uuid.uuid4().hex}.pdf'
    #     pdf_path = os.path.join(settings.TEMPORARY_ROOT, pdf_name)
    #     pdf_file = Path(pdf_path)
    #     pdf_file.touch(exist_ok=True)
    #     # create a new pdf
    #     pdf_doc = fitz.open()
    #     # decompress zip file
    #     img_path = self.decompress(zip_file)
    #     try:
    #         for img in sorted(glob.glob(os.path.join(img_path, '*'))):
    #             # todo 解密图片
    #             # insert
    #             img_doc = fitz.open(img)
    #             pdf_bytes = img_doc.convert_to_pdf()
    #             img_pdf = fitz.open('pdf', pdf_bytes)
    #             pdf_doc.insert_pdf(img_pdf)
    #         pdf_doc.ez_save(pdf_file)
    #     except Exception as e:
    #         print(f'Exception when calling PDFHandler->save_pdf: {e}')
    #         raise
    #     finally:
    #         # delete images
    #         self.remove(img_path)
    #         # delete zip file
    #         if isinstance(zip_file, str):
    #             self.remove(zip_file)
    #         # close pdf doc
    #         pdf_doc.close()
    #     return pdf_file

    def get_img_urls(self, token_url: str, cid: str) -> list:
        # 1, get files according to cid
        data = NFTStorageHandler().retrieve(cid)
        # sort urls to ordering pages
        urls = sorted([os.path.join(token_url, file['name']) for file in data['files']])
        return urls

    def get_pdf(self, token_url: str, cid: str) -> str:
        urls = self.get_img_urls(token_url, cid)
        # 2, download file by url
        img_dir = self.download_images(urls)
        # convert images to pdf
        file = self.to_pdf(img_dir)
        return file

    def get_preview_doc(self, from_page: int = 0, to_page: int = 4) -> str:
        """
        get a piece of original pdf
        :param from_page: int
        :param to_page: int
        :return: str, file path
        """
        assert from_page <= to_page, 'The from page must be no larger than to page'
        # create a new pdf
        # create directory if not exists
        os.makedirs(settings.PREVIEW_DOC_ROOT, exist_ok=True)
        # create file
        file_name = f'{uuid.uuid4().hex}.pdf'
        file_path = os.path.join(settings.PREVIEW_DOC_ROOT, file_name)
        file = Path(file_path)
        file.touch(exist_ok=True)
        # insert page to new pdf
        preview_doc = fitz.open()
        try:
            preview_doc.insert_pdf(self.pdf, from_page=from_page, to_page=to_page)
            # save file
            preview_doc.ez_save(file_path)
        except Exception as e:
            print(f'Exception when calling PDFHandler->get_preview_doc: {e}')
            raise
        finally:
            preview_doc.close()
        return f'{settings.PREVIEW_DIR}/{file_name}'

# if __name__ == '__main__':
# #     # pdf_file = '../pdf/test.pdf'
# #     # img_dir = '../pdf/img'
# #     # pdf2img(pdf_file, img_dir)
# #     path = '../tmp/53f212d5abe248bb8584ede9a00f8f91/'
# #     # zip_file = '../media/23857ec810ce425190112467e71b74e0.zip'
# #     zip_file_path = FileHandler.compress(path)
# #     print(zip_file_path)
# #     print(FileHandler.decompress(zip_file_path))
#     zip_file = '../media/90b713203c5b45329ae4404b94accfc8.zip'
#     print(PDFHandler.save_pdf(zip_file))
