from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


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
        address = '0x' + '0' * 40

        if username and password:
            model_user = get_user_model()
            try:
                print('Get super user...')
                model_user.objects.get(username=username)
            except model_user.DoesNotExist:
                print('Super user not found...')
                model_user.objects.create_superuser(username=username, password=password, email=email,
                                                    address=address)
        else:
            raise ValueError('Please give the username and password,')
