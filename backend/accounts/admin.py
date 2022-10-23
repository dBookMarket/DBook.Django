from django.contrib import admin
from . import models

from django.urls import path
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.shortcuts import render

import accounts.views


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
        return render(request, "admin/assign_issue_perm.html",
                      {'users': queryset, 'action': 'Add', 'contract': {
                          'platform_address': settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ADDRESS'],
                          'platform_abi': settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ABI']
                      }})

    @admin.action(description='remove issue permission')
    def remove_issue_perm(self, request, queryset):
        return render(request, "admin/assign_issue_perm.html",
                      {'users': queryset, 'action': 'Remove', 'contract': {
                          'platform_address': settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ADDRESS'],
                          'platform_abi': settings.CONTRACT_SETTINGS['PLATFORM_CONTRACT_ABI']
                      }})

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
                   path('login-with-metamask/', accounts.views.LoginWithMetaMaskView.as_view(),
                        name='%s_%s_metamask' % info),
                   path('issue-perm/', accounts.views.IssuePermView.as_view(), name='%s_%s_issue_perm' % info)
               ] + super().get_urls()


class SocialMediaAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_id', 'username', 'type', 'shared']
    search_fields = ['user__account_addr', 'account_id', 'username', 'type']


admin.site.register(models.User, UserAdmin)
admin.site.register(models.SocialMedia)

admin.site.site_header = "D-BOOK Admin"
