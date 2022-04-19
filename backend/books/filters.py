import django_filters
from . import models


class AssetFilter(django_filters.FilterSet):
    class Meta:
        model = models.Asset
        fields = ['issue']

    @property
    def qs(self):
        parent = super().qs
        user = getattr(self.request, 'user', None)

        return parent.filter(user=user) & parent.filter(amount__gt=0)
