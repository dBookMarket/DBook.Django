from rest_framework.permissions import IsAuthenticated
from . import models, serializers, filters
from utils.views import BaseViewSet


class NotificationViewSet(BaseViewSet):
    serializer_class = serializers.NotificationSerializer
    queryset = models.Notification.objects.all()
    filterset_class = filters.NotificationFilter
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'delete']
