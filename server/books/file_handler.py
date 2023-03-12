import fitz
import os
import shutil
from io import BytesIO
import zipfile
from django.conf import settings
from pathlib import Path
import uuid
from ebooklib import epub
from weasyprint import HTML
from epubconverter import epub_to_pdf


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


class EPUBHandler(FileHandler):

    def __init__(self, file: str):
        """
        :param file: str, the absolute path of file
        """
        self.filename = file
        # ERROR Relative URI reference without a base URI: <link href="css/idGeneratedStyles.css">
        self.book = epub.read_epub(file, options={'ignore_ncx': True})

    def get_pages(self):
        return 0

    def get_file_name(self) -> str:
        try:
            _title = self.book.get_metadata('DC', 'title')[0][0]
            return _title.replace(' ', '-')
        except Exception as e:
            print(f'Exception when get file name->{e}')
            return uuid.uuid4().hex
    
    def get_preview_doc(self, from_page: int = 0, to_page: int = 4):
        """
        get a piece of original file
        :param from_page: int
        :param to_page: int
        :return: str, file path
        """
        file_name = f'{self.get_file_name()}.pdf'
        file_path = os.path.join(settings.TEMPORARY_ROOT, file_name)

        # contents = ''
        # for doc in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        #     contents += doc.content.decode()

        # contents = self.beautify()
        # print(f'-----------=-=-=============={contents}')
        # HTML(string=contents).write_pdf(file_path)
        epub_to_pdf(self.filename, file_path)

        try:
            pdf_handler = PDFHandler(file_path)
            pre_doc_path = pdf_handler.get_preview_doc(from_page, to_page)
        finally:
            self.remove(file_path)

        return pre_doc_path


class TextHandler(FileHandler):

    def __init__(self, file: str):
        """
        :param file: str, the absolute path of file
        """
        self.file = open(file, 'rb')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()

    def get_pages(self):
        return 0

    def get_file_name(self) -> str:
        return uuid.uuid4().hex

    def get_preview_doc(self, from_page: int = 0, to_page: int = 4):
        """
        get a piece of original file
        :param from_page: int
        :param to_page: int
        :return: str, file path
        """
        file_name = f'{self.get_file_name()}.pdf'
        file_path = os.path.join(settings.TEMPORARY_ROOT, file_name)

        content = b''
        chunk_size = 512
        chunk = self.file.readline(chunk_size)
        while chunk:
            content += chunk
            chunk = self.file.readline(chunk_size)

        HTML(string=content.decode()).write_pdf(file_path)

        try:
            pdf_handler = PDFHandler(file_path)
            pre_doc_path = pdf_handler.get_preview_doc(from_page, to_page)
        finally:
            self.remove(file_path)

        return pre_doc_path


class FileHandlerFactory:

    def __new__(cls, _type: str, file, *args, **kwargs):
        if _type == 'pdf':
            return PDFHandler(file)
        elif _type == 'epub':
            return EPUBHandler(file)
        elif _type == 'txt':
            return TextHandler(file)
        else:
            raise TypeError(f'Type {_type} is not supported.')
