import django_filters
from . import models


class TradeFilter(django_filters.FilterSet):
    class Meta:
        model = models.Trade
        fields = ['issue', 'user']


class TransactionFilter(django_filters.FilterSet):
    class Meta:
        model = models.Transaction
        fields = ['trade', 'buyer', 'trade__user', 'trade__issue', 'issue', 'seller']
