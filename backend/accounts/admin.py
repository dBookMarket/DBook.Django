from django.contrib import admin
from . import models

from django.contrib.auth.models import Permission
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.shortcuts import render

import json


class UserAdmin(BaseUserAdmin, ModelBackend):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'name', 'desc', 'type')}),
        (_('Wallet info'), {'fields': ('account_addr', 'wallet_addr')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('account_addr', 'wallet_addr', 'name', 'type', 'email', 'has_issue_perm')
    search_fields = ('name', 'account_addr', 'email')
    actions = ['assign_issue_perm', 'remove_issue_perm']

    @admin.action(description='assign issue permission')
    def assign_issue_perm(self, request, queryset):
        # try:
        #     issue_perm = Permission.objects.get(codename='add_issue')
        #     for user in queryset:
        #         user.user_permissions.add(issue_perm)
        return render(request, "admin/assign_issue_perm.html",
                      {'users': queryset, 'action': 'Add', 'contract': {
                          'platform_address': settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ADDRESS'],
                          'platform_abi': settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ABI']
                      }})

    # except Permission.DoesNotExist:
    #     self.message_user(request, _('Permission not found, cannot assign it to user.'))

    @admin.action(description='remove issue permission')
    def remove_issue_perm(self, request, queryset):
        # try:
        #     issue_perm = Permission.objects.get(codename='add_issue')
        #     for user in queryset:
        #         user.user_permissions.remove(issue_perm)
        return render(request, "admin/assign_issue_perm.html",
                      {'users': queryset, 'action': 'Remove', 'contract': {
                          'platform_address': settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ADDRESS'],
                          'platform_abi': settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ABI']
                      }})
    # except Permission.DoesNotExist:
    #     self.message_user(request, _('Permission not found, cannot assign it to user.'))


admin.site.register(models.User, UserAdmin)

admin.site.site_header = "D-BOOK Admin"
