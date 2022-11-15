import books.models
from tests.base import config
from http import HTTPStatus

BASE_URL = f'{config["api"]}/banners'


def test_get(db, client):
    books.models.Banner.objects.create(**{
        'name': 'bbb',
        'desc': 'bbb',
        'redirect_url': 'https://test.banner.com'
    })
    response = client.get(f'{BASE_URL}?name=bbb')
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['name'] == 'bbb'
    assert response.data['results'][0]['desc'] == 'bbb'
    assert response.data['results'][0]['redirect_url'] == 'https://test.banner.com'
