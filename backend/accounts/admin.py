from django.contrib import admin
from . import models

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext, gettext_lazy as _


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
    list_display = ('account_addr', 'wallet_addr', 'name', 'type', 'email')
    search_fields = ('name', 'account_addr', 'email')


admin.site.register(models.User, UserAdmin)
