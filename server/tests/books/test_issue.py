import books.models
import stores.models
from tests.base import config
from http import HTTPStatus
from tests import helper
from utils.enums import IssueStatus

BASE_URL = f'{config["api"]}/issues'


# def setup_module(module):
#     print('-----setup------')
#
#
# def teardown_module(module):
#     print('-----teardown-----')


def test_create(admin_client, client, default_category, default_user):
    response = client.post(BASE_URL)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    response = admin_client.post(BASE_URL)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'category' in response.data
    assert 'author_name' in response.data
    assert 'cover' in response.data
    assert 'name' in response.data
    assert 'desc' in response.data
    assert 'file' in response.data
    assert 'amount' in response.data
    assert 'price' in response.data
    assert 'publisher_name' in response.data
    response = admin_client.post(BASE_URL, data={
        'category': default_category.id,
        'author_name': 'aaa',
        'name': 'issue1',
        'desc': 'issue1',
        'cover': helper.generate_photo_file(),
        'amount': 10,
        'price': 1,
        'file': helper.generate_pdf_file(),
        'publisher_name': 'bbb',
        'ratio': 0.25,
        'cids': [
            'abcdefg',
            '1234567'
        ]
    }, format='multipart')
    assert response.status_code == HTTPStatus.CREATED
    assert response.data['category'] == default_category.id
    assert response.data['author_name'] == 'aaa'
    assert response.data['author_desc'] == ''
    assert response.data['name'] == 'issue1'
    assert response.data['desc'] == 'issue1'
    assert response.data['amount'] == 10
    assert response.data['price'] == 1
    assert response.data['ratio'] == 0.25
    assert response.data['publisher']['name'] == 'bbb'
    assert response.data['publisher']['desc'] == ''


def test_update(admin_client, client, default_issue):
    response = client.put(f'{BASE_URL}/{default_issue.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    response = admin_client.patch(f'{BASE_URL}/{default_issue.id}', data={
        'name': 'book1'
    }, content_type='application/json')
    assert response.status_code == HTTPStatus.OK
    assert response.data['name'] == 'book1'
    assert response.data['category'] == default_issue.category_id
    assert response.data['author_name'] == default_issue.author_name
    assert response.data['author_desc'] == default_issue.author_desc
    assert response.data['desc'] == default_issue.desc
    assert response.data['amount'] == default_issue.amount
    assert response.data['price'] == default_issue.price
    assert response.data['publisher']['name'] == default_issue.publisher.name
    assert response.data['publisher']['desc'] == default_issue.publisher.desc


def test_get(client, default_issue):
    response = client.get(f'{BASE_URL}?name={default_issue.name}')
    assert response.status_code == HTTPStatus.OK
    assert len(response.data['results']) == 1
    assert response.data['count'] == 1
    assert response.data['results'][0]['name'] == default_issue.name
    assert response.data['results'][0]['cover_url'] == ''
    assert response.data['results'][0]['n_pages'] == default_issue.n_pages
    assert response.data['results'][0]['name'] == default_issue.name
    assert response.data['results'][0]['author_name'] == default_issue.author_name

    response = client.get(f'{BASE_URL}/{default_issue.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.data['name'] == default_issue.name
    assert response.data['category'] == default_issue.category_id
    assert response.data['author_name'] == default_issue.author_name
    assert response.data['author_desc'] == default_issue.author_desc
    assert response.data['desc'] == default_issue.desc
    assert response.data['amount'] == default_issue.amount
    assert response.data['price'] == default_issue.price
    assert response.data['publisher']['name'] == default_issue.publisher.name
    assert response.data['publisher']['desc'] == default_issue.publisher.desc
    assert response.data['contract'] == {}
    assert response.data['preview'] == {}
    assert response.data['cover_url'] == ''
    assert response.data['price_range']['min_price'] == 20
    assert response.data['price_range']['max_price'] == 40
    assert response.data['n_remains'] == 0


def test_delete(admin_client, client, default_issue):
    response = client.delete(f'{BASE_URL}/{default_issue.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = admin_client.delete(f'{BASE_URL}/{default_issue.id}')
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_trade(auth_client, client, default_user, default_category):
    response = auth_client.post(BASE_URL, data={
        'category': default_category.id,
        'author_name': 'aaa',
        'name': 'issue1',
        'desc': 'issue1',
        'cover': helper.generate_photo_file(),
        'amount': 10,
        'price': 1,
        'file': helper.generate_pdf_file(),
        'publisher_name': 'bbb',
    }, format='multipart')
    issue_id = response.data['id']
    obj = books.models.Issue.objects.get(id=issue_id)
    obj.status = IssueStatus.UPLOADED.value
    obj.save()

    response = auth_client.put(f'{BASE_URL}/{issue_id}/trade')
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'address' in response.data

    response = auth_client.put(f'{BASE_URL}/{issue_id}/trade', data={
        "address": "0x1234567890abcd",
        "token_criteria": 'ERC-1155',
        'block_chain': 'Polygon',
        'token': 'USDT',
        'token_amount': 5
    })
    assert response.status_code == HTTPStatus.OK
    response = client.get(f'{BASE_URL}?name={obj.name}')
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['status'] == IssueStatus.SUCCESS.value
    # contract
    obj_contract = books.models.Token.objects.get(issue_id=issue_id)
    assert obj_contract.address == '0x1234567890abcd'
    assert obj_contract.token_amount == 5
    assert obj_contract.token_criteria == 'ERC-1155'
    assert obj_contract.block_chain == 'Polygon'
    assert obj_contract.token == 'USDT'
    # preview
    obj_preview = books.models.Preview.objects.get(issue_id=issue_id)
    assert obj_preview.start_page == 1
    assert obj_preview.n_pages == 5
    assert obj_preview.file is not None
    # trade
    obj_trades = stores.models.Trade.objects.filter(issue_id=issue_id)
    assert len(obj_trades) == 1
    assert obj_trades.first().amount == obj.amount
    assert obj_trades.first().price == obj.price
    assert obj_trades.first().first_release
    # asset
    obj_assets = books.models.Asset.objects.filter(user=default_user, issue_id=issue_id)
    assert len(obj_assets) == 1
    assert obj_assets.first().amount == obj.amount


def test_get_current_issue(auth_client, uploaded_issue):
    response = auth_client.get(f'{BASE_URL}/current')
    assert response.status_code == HTTPStatus.OK
    assert response.data['category'] == uploaded_issue.category_id
    assert response.data['author_name'] == uploaded_issue.author_name
    assert response.data['author_desc'] == uploaded_issue.author_desc
    assert response.data['name'] == uploaded_issue.name
    assert response.data['desc'] == uploaded_issue.desc
    assert response.data['amount'] == uploaded_issue.amount
    assert response.data['price'] == uploaded_issue.price
    assert response.data['ratio'] == uploaded_issue.ratio
    assert response.data['status'] == uploaded_issue.status
    assert response.data['publisher']['name'] == uploaded_issue.publisher.name
    assert response.data['publisher']['desc'] == uploaded_issue.publisher.desc


def test_get_current_issue_with_first_one(auth_client):
    response = auth_client.get(f'{BASE_URL}/current')
    assert response.status_code == HTTPStatus.OK
    assert response.data['category'] is None
    assert response.data['author_name'] == ''
    assert response.data['author_desc'] == ''
    assert response.data['name'] == ''
    assert response.data['desc'] == ''
    assert response.data['amount'] is None
    assert response.data['price'] is None
    assert response.data['cover'] is None
    assert response.data['file'] is None
    assert response.data['ratio'] is None
    assert response.data['publisher_name'] == ''
    assert response.data['publisher_desc'] == ''
