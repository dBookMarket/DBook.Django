from PIL import Image
import io
import fitz
from tests.base import config
from books.models import Issue
from utils.enums import IssueStatus


def trade_book(auth_client, default_category):
    response = auth_client.post(f'{config["api"]}/issues', data={
        'category': default_category.id,
        'author_name': 'aaa',
        'name': 'issue1',
        'desc': 'issue1',
        'cover': generate_photo_file(),
        'amount': 10,
        'price': 1,
        'file': generate_pdf_file(),
        'publisher_name': 'bbb',
    }, format='multipart')
    issue_id = response.data['id']
    obj = Issue.objects.get(id=issue_id)
    obj.status = IssueStatus.UPLOADED.value
    obj.save()

    auth_client.put(f'{config["api"]}/issues/{issue_id}/trade', data={
        "address": "0x1234567890abcd",
        "token_criteria": 'ERC-1155',
        'block_chain': 'Polygon',
        'token': 'USDT',
        'token_amount': 5
    })
    return obj


def generate_photo_file():
    file = io.BytesIO()
    image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
    image.save(file, 'png')
    file.name = 'test.png'
    file.seek(0)
    return file


def generate_pdf_file():
    file = io.BytesIO()
    doc = fitz.open()
    page = doc.new_page()
    where = fitz.Point(10, 100)
    page.insert_text(where, 'test pdf', fontsize=50)
    doc.save(file)
    file.name = 'test.pdf'
    file.seek(0)
    return file
