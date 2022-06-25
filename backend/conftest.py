import pytest
import books.models
import accounts.models
from utils.enums import IssueStatus
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Permission


@pytest.fixture(scope='session')
def django_db_setup():
    pass


@pytest.fixture
def default_category(db):
    return books.models.Category.objects.create(parent=None, name='novel', comment='novel')


@pytest.fixture
def default_user(db):
    obj = accounts.models.User.objects.create_user(username='seller', account_addr="abcd")
    issue_perm = Permission.objects.get(codename='add_issue')
    obj.user_permissions.add(issue_perm)
    return obj


@pytest.fixture
def normal_user(db):
    return accounts.models.User.objects.create_user(username='buyer', account_addr="1234")


@pytest.fixture
def auth_client(db, default_user):
    token, _ = Token.objects.get_or_create(user=default_user)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.key)
    return api_client


@pytest.fixture
def auth_client_with_normal_user(db, normal_user):
    token, _ = Token.objects.get_or_create(user=normal_user)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.key)
    return api_client


@pytest.fixture
def default_issue(db, default_user, default_category):
    return books.models.Issue.objects.create(**{
        'category': default_category,
        'author_name': 'aaa',
        'name': 'issue1',
        'desc': 'issue1',
        'amount': 10,
        'price': 1,
        'publisher': default_user,
        'status': IssueStatus.SUCCESS.value
    })


@pytest.fixture
def uploaded_issue(db, default_user, default_category):
    instance = books.models.Issue.objects.create(**{
        'category': default_category,
        'author_name': 'aaa',
        'name': 'issue1',
        'desc': 'issue1',
        'amount': 10,
        'price': 1,
        'publisher': default_user,
        'status': IssueStatus.UPLOADED.value
    })
    return instance
