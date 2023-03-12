from books.file_handler import EPUBHandler
from pathlib import Path
import os

test_dir = Path(__file__).resolve().parent.parent


def test_epub_handler():
    file_path = os.path.join(test_dir, 'jp.epub')
    handler = EPUBHandler(file_path)
    new_path = handler.get_preview_doc(0, 20)
    assert new_path

