import django_filters
from . import models
from utils.enums import IssueStatus


class IssueFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = models.Issue
        fields = ['category', 'publisher', 'publisher__account_addr', 'name']

    @property
    def qs(self):
        parent = super().qs
        return parent.filter(status=IssueStatus.SUCCESS.value)


class AssetFilter(django_filters.FilterSet):
    class Meta:
        model = models.Asset
        fields = ['issue']

    @property
    def qs(self):
        parent = super().qs
        user = getattr(self.request, 'user', None)

        return parent.filter(user=user, amount__gt=0)


class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        models = models.Category
        fields = ['parent', 'name', 'level']


class BannerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        models = models.Banner
        fields = ['name']
