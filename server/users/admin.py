from django.contrib import admin
from . import models

from django.urls import path
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.shortcuts import render

import users.views


class UserAdmin(BaseUserAdmin, ModelBackend):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': (
         'avatar', 'banner', 'first_name', 'last_name', 'email', 'name', 'desc', 'website_url', 'discord_url')
        }),
        (_('Wallet info'), {'fields': ('address',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('id', 'address', 'name', 'email', 'is_verified')
    search_fields = ('name', 'address', 'email')
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
                   path('login-with-metamask/', users.views.LoginWithMetaMaskView.as_view(),
                        name='%s_%s_metamask' % info),
                   path('issue-perm/', users.views.IssuePermView.as_view(), name='%s_%s_issue_perm' % info)
               ] + super().get_urls()


class AccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_id', 'username', 'type', 'shared']
    search_fields = ['user__address', 'account_id', 'username', 'type']


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Account, AccountAdmin)
admin.site.register(models.Fans)

admin.site.site_header = "D-BOOK Admin"
