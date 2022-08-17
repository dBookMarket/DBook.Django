from rest_framework.authtoken.views import APIView
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from django.core.exceptions import ObjectDoesNotExist
from django.contrib import auth
from django.contrib.auth.models import Permission, AnonymousUser

from accounts.models import User, SocialMedia
from accounts.serializers import UserSerializer
from web3 import Web3

from . import filters

from utils.helper import Helper
from utils.social_media_handler import SocialMediaFactory, DuplicationError, RequestError
from utils.enums import UserType, SocialMediaType
from utils.smart_contract_handler import PlatformContractHandler


def validate_addr(addr: str):
    if not addr:
        raise ValidationError({'address': 'This field is required'})
    try:
        valid_addr = Web3.toChecksumAddress(addr)
    except ValueError:
        raise ValidationError({'address': 'Invalid wallet address'})
    return valid_addr


def create_user(addr: str) -> User:
    user, _ = User.objects.get_or_create(account_addr=addr, defaults={
        'username': Helper.rand_username()
    })
    return user


class NonceAPIView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        address = request.data.get('address', '')
        valid_addr = validate_addr(address)
        user = create_user(valid_addr)
        # user = get_user(address)
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
    permission_classes = [IsAuthenticatedOrReadOnly]
    base_cache_key = 'social_media'
    http_method_names = ['get', 'post', 'options']

    def validate_type(self, value: str):
        if not value:
            raise ValidationError({'type': 'This field is required'})
        sm_options = {member.value for member in SocialMediaType}
        if value not in sm_options:
            raise ValidationError({'type': f'This field must be one of {sm_options}'})

    @action(methods=['post'], detail=False, url_path='auth')
    def authenticate(self, request, *args, **kwargs):
        """
        API for authenticating social media account.
        """
        _type = request.data.get('type', '')
        self.validate_type(_type)

        handler = SocialMediaFactory.get_instance(_type)
        if not handler:
            raise ValidationError({'detail': 'Unknown error.'})

        try:
            auth_uri = handler.authenticate()
        except RequestError as e:
            raise ValidationError({'detail': str(e)})

        return Response({'auth_uri': auth_uri}, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=False, url_path='share')
    def share(self, request, *args, **kwargs):
        """
        API for creating a post with the user's social media account.
        """
        _user = request.user

        _type = request.data.get('type', '')
        self.validate_type(_type)

        _content = request.data.get('content', '')
        if not _content:
            raise ValidationError({'content': 'The sharing content should not be empty'})

        if _type == SocialMediaType.LINKEDIN.value:
            try:
                sm = SocialMedia.objects.get(user=_user, type=SocialMediaType.TWITTER.value)
                if not sm.shared:
                    raise ValidationError({'detail': 'Please verify twitter identification at first.'})
            except SocialMedia.DoesNotExist:
                raise ValidationError({'detail': 'Please verify twitter identification at first.'})

        if _type == SocialMediaType.TWITTER.value:
            token = request.data.get('oauth_token', '')
            verifier = request.data.get('oauth_verifier', '')
        else:
            token = request.data.get('code', '')
            verifier = request.data.get('state', '')

        handler = SocialMediaFactory.get_instance(_type)
        if not handler:
            raise ValidationError({'detail': 'Unknown error.'})

        try:
            handler.link_user_and_share(_user.account_addr, token, verifier, _content)
        except DuplicationError as e:
            raise ValidationError({'detail': str(e)})
        except RequestError as e:
            raise ValidationError({'detail': str(e)})
        except Exception as e:
            print(f'Fail to send share with {_type}, detail: {e}')
            raise ValidationError({'detail': 'Unknown error.'})

        if _type == SocialMediaType.LINKEDIN.value:
            # add issue perm
            self.add_author_perm()

        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)

    def add_author_perm(self):
        _user = self.request.user

        # add author perm into smart contract
        added = PlatformContractHandler().add_author(_user.account_addr)
        if not added:
            raise ValidationError({'detail': 'Fail to add perm from contract, please try later.'})

        # add issue perm
        try:
            issue_perm = Permission.objects.get(codename='add_issue')
        except Permission.DoesNotExist:
            print('Exception when calling add_author_perm -> permission `add_issue` not found')
            raise ValidationError({'detail': 'Fail to become an author, please ask system manager for help.'})

        _user.user_permissions.add(issue_perm)

        # change user type
        _user.type = UserType.AUTHOR.value
        _user.save()

    @action(methods=['get'], detail=False, url_path='verification-state')
    def check_status(self, request, *args, **kwargs):
        """
        Check the verification status.
        """
        _user = request.user

        res = {
            'linkedin': False,
            'twitter': False
        }

        if isinstance(_user, AnonymousUser):
            return Response(res)

        queryset = SocialMedia.objects.filter(user=_user)

        for obj in queryset:
            if obj.type == SocialMediaType.TWITTER.value:
                res['twitter'] = obj.shared
            if obj.type == SocialMediaType.LINKEDIN.value:
                res['linkedin'] = obj.shared

        return Response(res)
