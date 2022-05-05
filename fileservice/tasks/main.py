from .celery import app
from handlers.pdf_handler import PDFHandler


@app.task(name='upload_file', autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 3})
def upload_file(file_path: str, sk_file: str) -> dict:
    """
    upload a pdf book into nft.storage
    :param sk_file: str, private key file path
    :param file_path: str, pdf file path
    :return:
    """
    res = PDFHandler(file_path).upload(sk_file)
    return res


@app.task(name='get_file_urls')
def get_file_urls(cids: list) -> list:
    """
    get each page url of a book from nft.storage
    :param cids: nft cid
    :return: list of url
    """
    return PDFHandler().get_file_urls(cids)
