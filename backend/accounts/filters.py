import django_filters
from .models import User


class UserFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = User
        fields = ['type', 'name']

    @property
    def qs(self):
        parent = super().qs
        return parent.filter(is_superuser=False, is_staff=False)
