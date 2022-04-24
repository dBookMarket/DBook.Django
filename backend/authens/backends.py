from django.contrib.auth.backends import ModelBackend
from utils.helper import Helper
from accounts.models import User


class MetaMaskBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        address = kwargs.get('address', '')
        signature = kwargs.get('signature', '')
        try:
            user = User.objects.get(account_addr=address)
            if user.is_staff or user.is_superuser:
                signer = Helper.eth_recover(user.nonce, signature)
                if Helper.equal(address, signer):
                    return user
        except Exception as e:
            print(f'Exception when authenticate metamask login: {e}')
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
