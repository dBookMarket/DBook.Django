import django_filters
from .models import Notification


class NotificationFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    message = django_filters.CharFilter(field_name='message', lookup_expr='icontains')

    class Meta:
        model = Notification
        fields = ['title', 'message', 'is_read']

    @property
    def qs(self):
        user = self.request.user
        return super().qs.filter(receiver=user)
