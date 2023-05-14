import django_filters
from django.contrib.auth.models import AnonymousUser
from . import models


class TradeFilter(django_filters.FilterSet):
    class Meta:
        model = models.Trade
        fields = ['issue', 'user']

    @property
    def qs(self):
        return super().qs.filter(first_release=False)


class TransactionFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(field_name='issue__book__author')

    class Meta:
        model = models.Transaction
        fields = ['trade', 'buyer', 'trade__user', 'trade__issue', 'issue', 'seller', 'author']


class BenefitFilter(django_filters.FilterSet):
    class Meta:
        model = models.Benefit
        fields = ['user', 'transaction', 'currency']

    @property
    def qs(self):
        user = getattr(self.request, 'user')
        if isinstance(user, AnonymousUser):
            return {}
        return super().qs.filter(user=user)
