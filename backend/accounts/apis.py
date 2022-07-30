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
from utils.social_media_handler import SocialMediaFactory, DuplicationError
import pickle
from utils.enums import UserType
from utils.smart_contract_handler import PlatformContractHandler
from utils.cache import Cache


def get_user(addr: str) -> User:
    """
    Fetch user according to wallet address.
    """
    try:
        valid_addr = Web3.toChecksumAddress(addr)
    except ValueError:
        raise ValidationError({'address': 'Invalid wallet address'})

    user, _ = User.objects.get_or_create(account_addr=valid_addr, defaults={
        'username': Helper.rand_username()
    })
    return user


class NonceAPIView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        address = request.data.get('address')
        # try:
        #     address = Web3.toChecksumAddress(address)
        # except ValueError:
        #     raise ValidationError({'address': 'Invalid address'})
        # user, _ = User.objects.get_or_create(account_addr=address, defaults={
        #     'username': Helper.rand_username()
        # })
        user = get_user(address)
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


class SocialMediaViewSet(viewsets.ViewSet):
    permission_classes = []
    base_cache_key = 'social_media'
    http_method_names = ['post', 'options']

    @action(methods=['post'], detail=False, url_path='auth')
    def authenticate(self, request, *args, **kwargs):
        """
        API for authenticating social media account.
        args:
            type: str, one of options {twitter, linkedin}

            address: str, the user's wallet address from metamask

        return:
            auth_url: str
        """
        _type = request.data.get('type', '')
        if not _type:
            raise ValidationError({'type': 'This field is required'})

        address = request.data.get('address')
        user = get_user(address)

        handler = SocialMediaFactory.get_instance(_type)
        if not handler:
            return Response({'auth_url': ''})
        auth_url = handler.authenticate()
        # cache handler instance for posting
        bytes_obj = pickle.dumps(handler)
        Cache(request.session).set(f'{self.base_cache_key}-{_type}-{user.account_addr}', bytes_obj.decode())
        return Response({'auth_url': auth_url})

    @action(methods=['post'], detail=False, url_path='post')
    def post_msg(self, request, *args, **kwargs):
        """
        API for creating a post with the user's social media account.
        args:
            oauth_verifier: str, which is a parameter of api of the social media account

            address: str, the user's wallet address from metamask

        return:
            status: str
        """
        address = request.data.get('address')
        user = get_user(address)

        _type = request.data.get('type', '')

        _verifier = request.data.get('oauth_verifier', '')
        str_obj = Cache(request.session).get(f'{self.base_cache_key}-{_type}-{user.account_addr}')
        if not str_obj:
            raise ValidationError({'Sorry, you should grant your social media account firstly.'})

        handler = pickle.loads(str_obj.encode())
        if not handler:
            return Response({'status': 'failure'})

        try:
            handler.create_msg(user.account_addr, oauth_verifier=_verifier)
        except DuplicationError as e:
            raise ValidationError(detail=str(e))

        # add issue perm
        self.add_author_perm(user)

        return Response({'status': 'success'})

    def add_author_perm(self, user):
        added = PlatformContractHandler().add_author(user.account_addr)
        if not added:
            raise ValidationError(detail='Fail to become an author, please retry later.')

        # add issue perm
        try:
            issue_perm = Permission.objects.get(codename='add_issue')
        except Permission.DoesNotExist:
            print('Exception when calling add_author_perm -> Permission add_issue not found')
            raise ValidationError(detail='Fail to become an author, please ask system manager for help.')
        user.user_permissions.add(issue_perm)

        # change user type
        user.type = UserType.AUTHOR.value
        user.save()

    @action(methods=['post'], detail=False, url_path='verify')
    def verify(self, request, *args, **kwargs):
        """
        API for verifying if the user create the post or not.
        If the user did, then call the smart contract to grant the user with author permissions.

        args:
            type: str, one of options {twitter, linkedin}

            address: str, the user's wallet address from metamask

        """
        address = request.data.get('address')
        user = get_user(address)

        _type = request.data.get('type', '')
        if not _type:
            raise ValidationError({'type': 'This field is required'})

        handler = SocialMediaFactory.get_instance(_type)
        if not handler:
            return Response({'status': 'failure'})

        # check the post
        success = handler.verify_msg(user.account_addr)
        if not success:
            raise ValidationError(detail='Please link to your social media account and post a message firstly.')

        self.add_author_perm(user)

        return Response({'status': 'success'})



