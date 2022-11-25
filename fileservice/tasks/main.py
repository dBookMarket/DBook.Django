from .celery import app
from handlers.pdf_handler import PDFHandler, FileHandler


@app.task(name='upload_file', autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 3})
def upload_file(file_path: str) -> dict:
    """
    upload a pdf book into nft.storage
    :param file_path: str, pdf file path
    :return:
    """
    # res = PDFHandler(file_path).upload()
    res = FileHandler().upload(file_path)
    return res


@app.task(name='get_file_urls')
def get_file_urls(cids: list) -> list:
    """
    get each page url of a book from nft.storage
    :param cids: nft cid
    :return: list of url
    """
    return PDFHandler().get_file_urls(cids)


@app.task(name='download_file', autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 3})
def download_file(file_path: str, cid: str, key: str) -> str:
    """
    download file from nft.storage
    :param file_path: the file_path for saving downloaded file
    :param cid: the file id in nft.storage
    :param key: the secret key for decrypt downloaded file

    :return: str, the path of decrypted file
    """
    decrypted_file = FileHandler().download(path=file_path, cid=cid, key=key)
    return decrypted_file
