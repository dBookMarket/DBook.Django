from rest_framework.authtoken.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework.authtoken.models import Token
from django.contrib import auth
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import User
from web3 import Web3
from utils.helper import Helper


class NonceAPIView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        address = request.data.get('address')
        try:
            address = Web3.toChecksumAddress(address)
        except ValueError:
            raise ValidationError({'address': 'Invalid address'})
        user, _ = User.objects.get_or_create(account_addr=address, defaults={
            'username': Helper.rand_username()
        })
        print('user', user)
        new_nonce = Helper.rand_nonce()
        print('nonce', new_nonce)
        user.nonce = new_nonce
        user.save()
        return Response({'nonce': new_nonce})


class LoginAPIView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        return self.authenticate(request)

    @staticmethod
    def authenticate(request):
        account_addr = request.data.get('address')
        signature = request.data.get('signature')
        try:
            user = User.objects.get(account_addr=account_addr)
            signer = Helper.eth_recover(user.nonce, signature)
            print('signer: ', signer)
            if account_addr == signer:
                token, _ = Token.objects.get_or_create(user=user)
                # update nonce
                user.nonce = Helper.rand_nonce()
                user.save()
                return Response({'token': token.key})
            else:
                raise ValidationError({'detail': 'Authentication fail'})
        except Exception:
            raise ValidationError({'detail': 'Authentication fail'})


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        return self.logout(request)

    @staticmethod
    def logout(request):
        try:
            request.user.auth_token.delete()
        except (AttributeError, ObjectDoesNotExist):
            pass
        # logout for django backend
        auth.logout(request)
        return Response({"detail": "Logout success."}, status=status.HTTP_200_OK)
