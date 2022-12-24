import django_filters
from . import models
from django.contrib.auth.models import AnonymousUser


class DraftFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = models.Draft
        fields = ['title']

    @property
    def qs(self):
        parent = super().qs
        user = getattr(self.request, 'user', None)
        if isinstance(user, AnonymousUser):
            return {}
        return parent.filter(author=user)


class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    desc = django_filters.CharFilter(field_name='desc', lookup_expr='icontains')

    class Meta:
        model = models.Book
        fields = ['title', 'desc']

    @property
    def qs(self):
        parent = super().qs
        user = getattr(self.request, 'user', None)
        if isinstance(user, AnonymousUser):
            return {}
        return parent.filter(author=user)


class IssueFilter(django_filters.FilterSet):
    class Meta:
        model = models.Issue
        fields = ['book']


class AssetFilter(django_filters.FilterSet):
    class Meta:
        model = models.Asset
        fields = ['issue']

    # @property
    # def qs(self):
    #     parent = super().qs
    #     user = getattr(self.request, 'user', None)
    #     if isinstance(user, AnonymousUser):
    #         return {}
    #     return parent.filter(user=user, quantity__gt=0)


class WishlistFilter(django_filters.FilterSet):
    class Meta:
        model = models.Wishlist
        fields = ['issue', 'user']


class AdvertisementFilter(django_filters.FilterSet):
    class Meta:
        model = models.Advertisement
        fields = ['show', 'issue']

    @property
    def qs(self):
        return super().qs.filter(show=True)
