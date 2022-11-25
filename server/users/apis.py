from rest_framework.authtoken.views import APIView
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from django.core.exceptions import ObjectDoesNotExist
from django.contrib import auth
from django.contrib.auth.models import Permission, AnonymousUser, Group

from users.models import User, Account, Fans
from users.serializers import UserSerializer, FansSerializer
from web3 import Web3

from . import filters

from utils.helpers import Helper
from utils.social_media_handler import SocialMediaFactory, DuplicationError, RequestError, TwitterHandler
from utils.enums import UserType, SocialMediaType
from utils.smart_contract_handler import PlatformContractHandler
from utils.views import BaseViewSet


def validate_addr(addr: str):
    if not addr:
        raise ValidationError({'address': 'This field is required'})
    try:
        valid_addr = Web3.toChecksumAddress(addr)
    except ValueError:
        raise ValidationError({'address': 'Invalid wallet address'})
    return valid_addr


def create_user(addr: str) -> User:
    user, _ = User.objects.get_or_create(address=addr, defaults={
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
        address = request.data.get('address')
        signature = request.data.get('signature')
        try:
            user = User.objects.get(address=address)
            signer = Helper.eth_recover(user.nonce, signature)
            print('signer: ', signer)
            if Helper.equal(address, signer):
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


class UserViewSet(BaseViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'put', 'patch']

    # filterset_class = filters.UserFilter

    # @action(methods=['POST', 'DELETE'], detail=True, url_path='issue-perm')
    # def assign_issue_perm(self, request, *args, **kwargs):
    #     user = self.get_object()
    #     try:
    #         issue_perm = Permission.objects.get(codename='add_issue')
    #     except Permission.DoesNotExist:
    #         return Response(status=status.HTTP_404_NOT_FOUND)
    #     if request.method == 'POST':
    #         user.user_permissions.add(issue_perm)
    #     elif request.method == 'DELETE':
    #         user.user_permissions.remove(issue_perm)
    #     serializer = self.get_serializer(user, many=False)
    #     return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path='current', permission_classes=[IsAuthenticated])
    def get_current(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, many=False)
        return Response(serializer.data)

    @action(methods=['put', 'patch'], detail=False, url_path='auth')
    def authenticate(self, request, *args, **kwargs):
        """
        API for authenticating social media account.
        """
        handler = TwitterHandler()
        try:
            auth_uri = handler.authenticate()
        except RequestError as e:
            raise ValidationError({'detail': str(e)})

        return Response({'auth_uri': auth_uri})

    def add_author_perm(self):
        _user = self.request.user

        # add author perm into smart contract
        added = PlatformContractHandler().add_author(_user.address)
        if not added:
            raise ValidationError({'detail': 'Fail to add perm from contract, please try later.'})

        # add issue perm
        # role author
        group, created = Group.objects.get_or_create(name='author')
        try:
            draft_perm = Permission.objects.get(codename='add_draft')
            book_perm = Permission.objects.get(codename='add_book')
            issue_perm = Permission.objects.get(codename='add_issue')
        except Permission.DoesNotExist:
            print('Exception when calling add_author_perm -> permission `add_issue` not found')
            raise ValidationError({'detail': 'Fail to become an author, please ask system manager for help.'})

        if created:
            group.permissions.set([draft_perm, book_perm, issue_perm])

        _user.groups.add(group)
        _user.is_verified = True
        _user.save()

    @action(methods=['put', 'patch'], detail=False, url_path='share')
    def share(self, request, *args, **kwargs):
        """
        Verify the user's twitter account, if passed, assign the author permissions to him/her.
        """
        _user = request.user

        _content = request.data.get('content', '')
        if not _content:
            raise ValidationError({'content': 'This field is required'})

        token = request.data.get('oauth_token', '')
        verifier = request.data.get('oauth_verifier', '')

        handler = TwitterHandler()
        try:
            handler.link_user_and_share(_user.address, token, verifier, _content)
        except DuplicationError as e:
            raise ValidationError({'detail': str(e)})
        except RequestError as e:
            raise ValidationError({'detail': str(e)})
        except Exception as e:
            print(f'Fail to send share, detail: {e}')
            raise ValidationError({'detail': 'Unknown error.'})

        # add issue perm
        self.add_author_perm()

        return Response({'detail': 'success'})


class AccountViewSet(viewsets.ViewSet):
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

        handler = SocialMediaFactory(_type)
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
                sm = Account.objects.get(user=_user, type=SocialMediaType.TWITTER.value)
                if not sm.shared:
                    raise ValidationError({'detail': 'Please verify twitter identification at first.'})
            except Account.DoesNotExist:
                raise ValidationError({'detail': 'Please verify twitter identification at first.'})

        if _type == SocialMediaType.TWITTER.value:
            token = request.data.get('oauth_token', '')
            verifier = request.data.get('oauth_verifier', '')
        else:
            token = request.data.get('code', '')
            verifier = request.data.get('state', '')

        handler = SocialMediaFactory(_type)
        if not handler:
            raise ValidationError({'detail': 'Unknown error.'})

        try:
            handler.link_user_and_share(_user.address, token, verifier, _content)
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
        added = PlatformContractHandler().add_author(_user.address)
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
            'linkedin': {'shared': False, 'username': ''},
            'twitter': {'shared': False, 'username': ''}
        }

        if isinstance(_user, AnonymousUser):
            return Response(res)

        queryset = Account.objects.filter(user=_user)

        for obj in queryset:
            if obj.type == SocialMediaType.TWITTER.value:
                res['twitter'] = {'shared': obj.shared, 'username': obj.username}
            if obj.type == SocialMediaType.LINKEDIN.value:
                res['linkedin'] = {'shared': obj.shared, 'username': obj.username}

        return Response(res)


class FansViewSet(BaseViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Fans.objects.all()
    serializer_class = FansSerializer
    filterset_class = filters.FansFilter
    http_method_names = ['get', 'post', 'delete']

    @action(methods=['get'], detail=False, url_path='current', permission_classes=[IsAuthenticated])
    def list_current(self, request, *args, **kwargs):
        """
        Fetch current user's loved authors.
        """
        if not request.GET._mutable:
            request.GET._mutable = True
        request.GET['user'] = request.user
        return super().list(request, *args, **kwargs)

    @action(methods=['post'], detail=False, url_path='remove')
    def remove(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
