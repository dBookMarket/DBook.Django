from rest_framework.authtoken.views import APIView
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework.authtoken.models import Token
from django.contrib import auth
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import User
from accounts.serializers import UserSerializer
from web3 import Web3
from utils.helper import Helper
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from django.contrib.auth.models import Permission
from . import filters
from .twitter_handler import SocialAccountFactory
import pickle


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
        return Response({'nonce': new_nonce}, status=status.HTTP_201_CREATED)


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
            if Helper.equal(account_addr, signer):
                token, _ = Token.objects.get_or_create(user=user)
                # update nonce
                user.nonce = Helper.rand_nonce()
                user.save()
                return Response({'token': token.key}, status=status.HTTP_201_CREATED)
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
        return Response({"detail": "Logout success."}, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = filters.UserFilter

    @action(methods=['POST', 'DELETE'], detail=True, url_path='issue-perm')
    def assign_issue_perm(self, request, *args, **kwargs):
        user = self.get_object()
        try:
            issue_perm = Permission.objects.get(codename='add_issue')
        except Permission.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.method == 'POST':
            user.user_permissions.add(issue_perm)
        elif request.method == 'DELETE':
            user.user_permissions.remove(issue_perm)
        serializer = self.get_serializer(user, many=False)
        return Response(serializer.data)


class AccountViewSet(APIView):
    permissions = []
    cache_key = 'social_media_instance'

    @action(methods=['post'], detail=False, url_path='auth')
    def authenticate(self, request, *args, **kwargs):
        """
        API for authenticating social media account.
        args:
            type: str, one of options {twitter, linkedin}

        return:
            auth_url: str
        """
        _type = request.data['type']
        handler = SocialAccountFactory.get_instance(_type)
        if handler:
            auth_url = handler.auth_tweet()
            # cache handler instance for posting
            bytes_obj = pickle.dumps(handler)
            request.session[self.cache_key] = bytes_obj.decode('utf-8')
            return Response({'auth_url': auth_url})
        return Response({'auth_url': ''})

    @action(methods=['post'], detail=False, url_path='post')
    def post_msg(self, request, *args, **kwargs):
        """
        API for creating a post with the user's social media account.
        args:
            oauth_verifier: str, which is a parameter of api of the social media account

        return:
            auth_url: str
        """
        _type = request.data['type']
        _verifier = request.data['oauth_verifier']
        str_obj = request.session[self.cache_key]
        if not str_obj:
            raise ValidationError({'Sorry, you should grant your social media account firstly.'})
        handler = pickle.loads(str_obj.encode('utf-8'))
        if handler:
            data = handler.create_tweet(_verifier)
            return Response({'status': bool(data)})
        return Response({'status': False})

    @action(methods=['post'], detail=False, url_path='verify')
    def verify(self, request, *args, **kwargs):
        """
        API for verifying if the user create the post or not.
        If the user did, then call the smart contract to grant the user with author permissions.

        args:
            type: str, one of options {twitter, linkedin}
        """
        # todo how to link the user's account with social media account?
        #   step 1, need to check the user's identify with social media account
        #   step 2, check if the user send a post about dbook recently or not
        #   step 3, if the user did, call smart contract to add auth to the user
        pass
