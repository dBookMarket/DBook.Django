from tests.base import config
from http import HTTPStatus
from tests import helper
import books.models

BASE_URL = f'{config["api"]}/bookmarks'


def test_update(auth_client, client, default_user, default_category):
    obj = helper.trade_book(auth_client, default_category)
    auth_client.get(f'{config["api"]}/assets')
    obj_bookmark = books.models.Bookmark.objects.get(user=default_user, issue=obj)

    response = client.patch(f'{BASE_URL}/{obj_bookmark.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # the number of pages is 1
    response = auth_client.patch(f'{BASE_URL}/{obj_bookmark.id}', data={
        'current_page': 2
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'current_page' in response.data

    # todo no real entity, so the number of pages is 0
    # response = auth_client.patch(f'{BASE_URL}/{obj_bookmark.id}', data={
    #     'current_page': 1
    # })
    # print(response.data)
    # assert response.status_code == HTTPStatus.OK
    # assert response.data['current_page'] == 1
