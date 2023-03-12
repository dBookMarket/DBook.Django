import pdfkit
import os
from PyPDF2 import PdfFileMerger
from PyPDF2.utils import PdfReadError
# from pathlib import Path
from uuid import uuid4
import shutil
from django.conf import settings


class PDFManager(object):
    """
        This class carries operations on pdf files.

        It has the following methods:

        convert() --- Which converts each of the markup file
        passed in to pdf. Markup file should be html

        combine() --- Which merges all of the pdf files created by
        the convert method, creating a new file.

        del_pdf() --- Which deletes all the pdf files created by
        the convert method.

    """
    # base_dir = Path(__file__).resolve().parent
    base_dir = settings.TEMPORARY_ROOT

    def __init__(self, markup_files, style_files, pdf_filename):
        self.markup_files = markup_files
        self.style_files = style_files
        self.pdf_filename = pdf_filename

    def convert(self):
        _dir = os.path.join(self.base_dir, uuid4().hex)
        if not os.path.exists(_dir):
            os.mkdir(_dir)

        try:
            pdf_files = []
            for idx, each in enumerate(self.markup_files):
                # Prevent conversion process from showing terminal updates
                options = {"enable-local-file-access": None, "quiet": ""}
                _filename = os.path.join(_dir, f'{idx}.pdf')
                pdfkit.from_file(each, _filename, options=options)
                pdf_files.append(_filename)

            print('--- Sections converted to pdf')

            merger = PdfFileMerger()

            try:
                for pdf in pdf_files:
                    try:
                        merger.append(pdf, import_bookmarks=False)
                    except PdfReadError:
                        pass

                merger.write(self.pdf_filename)

                print('--- Sections combined together in a single pdf file')
            finally:
                merger.close()
        finally:
            shutil.rmtree(_dir)
            # for each in self.pdf_files:
            #     os.remove(each)
            print('--- Individual pdf files deleted from directory')
