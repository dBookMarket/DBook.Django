from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Create super user with command silently.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='user name')
        parser.add_argument('password', type=str, help='password')
        parser.add_argument('email', type=str, help='email')

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')
        email = options.get('email', '')

        # unique key
        account_addr = options.get('account_addr', '0x'+('0'*64))

        if username and password:
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                User.objects.create_superuser(username=username, password=password, email=email,
                                              account_addr=account_addr)
        else:
            raise ValueError('Please give the username and password,')
