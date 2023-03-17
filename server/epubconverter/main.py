from uuid import uuid4
import os
import shutil
import zipfile
from epubconverter.extractor import Extractor
from epubconverter.pdf_manager import PDFManager
from django.conf import settings


def epub_to_pdf(filename: str, pdf_filename: str):
    if not filename.endswith(".epub"):
        return

    zip_filename = "{}.zip".format(os.path.splitext(filename)[0])

    # zip file extracted directory
    # p_dir, _ = os.path.split(filename)
    extracted_dir = os.path.join(settings.TEMPORARY_ROOT, uuid4().hex)
    if not os.path.exists(extracted_dir):
        os.makedirs(extracted_dir)

    try:
        # convert epub to zip
        shutil.copyfile(filename, zip_filename)

        with zipfile.ZipFile(zip_filename) as f:
            f.extractall(extracted_dir)

        extractor = Extractor(extracted_dir)
        extractor.get_all()
        extractor.get_html()
        extractor.get_css()
        extractor.get_images()

        _html_files = extractor.html_files
        _style_files = extractor.css_files

        pdf = PDFManager(_html_files, _style_files, pdf_filename)
        pdf.convert()

    except Exception as e:
        print(f'Fail to convert epub to pdf, error -> {e}')
        raise
    finally:
        shutil.rmtree(extracted_dir)
        if os.path.exists(zip_filename):
            os.remove(zip_filename)


def html_to_epub():
    pass

# if __name__ == '__main__':
# 	_filename = '/home/future/workspace/DBook.Django/server/tests/test.epub'
# 	_pdf_filename = '/home/future/workspace/DBook.Django/server/tests/test001.pdf'
# 	epub_to_pdf(_filename, _pdf_filename)
