from .celery import app
from handlers.pdf_handler import PDFHandler


@app.task(name='upload_file')
def upload_file(file_path: str) -> dict:
    """
    upload a pdf book into nft.storage
    :param file_path: str
    :return:
    """
    res = PDFHandler(file_path).upload()
    return res


@app.task(name='get_file_urls')
def get_file_urls(cid: str) -> list:
    """
    get each page url of a book from nft.storage
    :param cid: nft cid
    :return: list of url
    """
    return PDFHandler().get_file_urls(cid)
