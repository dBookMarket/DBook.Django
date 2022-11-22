from django.contrib import admin
from . import models


class TradeAdmin(admin.ModelAdmin):
    list_display = ['id', 'book', 'quantity', 'price', 'first_release']
    search_fields = ['book__title']


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'trade', 'book', 'quantity', 'price', 'hash', 'status', 'seller', 'buyer', 'created_at']
    search_fields = ['book__title', 'hash', 'status', 'seller__name', 'buyer__name']


class BenefitAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'transaction', 'amount', 'currency']
    search_fields = ['user__name', 'transaction__hash', 'currency']


admin.site.register(models.Trade, TradeAdmin)
admin.site.register(models.Transaction, TransactionAdmin)
admin.site.register(models.Benefit, BenefitAdmin)
