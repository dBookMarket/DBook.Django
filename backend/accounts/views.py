from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views import generic
from django.urls import reverse
from django.contrib.auth.models import Permission
from .models import User
import json
from web3.auto import Web3
from utils.helper import Helper
from utils.enums import UserType


class LoginWithMetaMaskView(generic.View):

    def put(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except TypeError:
            data = request.body
        address = data.get('address')
        try:
            address = Web3.toChecksumAddress(address)
        except ValueError:
            return JsonResponse({'address': 'Invalid address'}, status=400)
        user, _ = User.objects.get_or_create(account_addr=address, defaults={
            'username': Helper.rand_username()
        })
        new_nonce = Helper.rand_nonce()
        user.nonce = new_nonce
        user.save()
        return JsonResponse({'nonce': new_nonce}, status=200)

    def post(self, request, *args, **kwargs):
        address = request.POST.get('address')
        signature = request.POST.get('signature')
        user = authenticate(request, address=address, signature=signature)
        if user:
            try:
                login(request, user)
                return JsonResponse({'detail': reverse('admin:index')}, status=200)
            except Exception as e:
                print(f'Exception when login with metamask: {e}')
                return JsonResponse({'detail': 'Login failed'}, status=400)
        return JsonResponse({'detail': 'You cannot access this site'}, status=403)


class IssuePermView(generic.View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except TypeError:
            data = request.body
        users = data.get('users', [])
        queryset = User.objects.filter(id__in=users)
        print('users', queryset)
        try:
            issue_perm = Permission.objects.get(codename='add_issue')
            for user in queryset:
                user.user_permissions.add(issue_perm)
            queryset.update(type=UserType.PUBLISHER.value)
            return JsonResponse({'detail': reverse('admin:accounts_user_changelist')}, status=200)
        except Permission.DoesNotExist:
            print('Permission not found when calling IssuePermView->post')
            return JsonResponse({'detail': 'Permission not found'}, status=400)

    def put(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except TypeError:
            data = request.body
        users = data.get('users', [])
        queryset = User.objects.filter(id__in=users)
        try:
            issue_perm = Permission.objects.get(codename='add_issue')
            for user in queryset:
                user.user_permissions.remove(issue_perm)
            queryset.update(type=UserType.PUBLISHER.value)
            return JsonResponse({'detail': reverse('admin:accounts_user_changelist')}, status=200)
        except Permission.DoesNotExist:
            print('Permission not found when calling IssuePermView->post')
            return JsonResponse({'detail': 'Permission not found'}, status=400)
