import pytest
import books.models
import users.models
from utils.enums import IssueStatus
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Permission


@pytest.fixture(scope='session')
def django_db_setup():
    pass


@pytest.fixture
def default_user(db):
    obj = users.models.User.objects.create_user(username='seller', address="abcd")
    issue_perm = Permission.objects.get(codename='add_issue')
    obj.user_permissions.add(issue_perm)
    return obj


@pytest.fixture
def normal_user(db):
    return users.models.User.objects.create_user(username='buyer', address="1234")


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
def default_issue(db, default_user):
    return books.models.Issue.objects.create(**{
        'author_name': 'aaa',
        'name': 'issue1',
        'desc': 'issue1',
        'amount': 10,
        'price': 1,
        'publisher': default_user,
        'status': IssueStatus.SUCCESS.value
    })


@pytest.fixture
def uploaded_issue(db, default_user):
    instance = books.models.Issue.objects.create(**{
        'author_name': 'aaa',
        'name': 'issue1',
        'desc': 'issue1',
        'amount': 10,
        'price': 1,
        'publisher': default_user,
        'status': IssueStatus.UPLOADED.value
    })
    return instance
