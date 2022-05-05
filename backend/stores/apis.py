from . import models, serializers, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions
from utils.views import BaseViewSet


class TradeViewSet(BaseViewSet):
    queryset = models.Trade.objects.all()
    serializer_class = serializers.TradeSerializer
    filterset_class = filters.TradeFilter

    def get_permissions(self):
        if self.action in {'update', 'destroy', 'partial_update'}:
            self.permission_classes = [DjangoObjectPermissions]
        return super().get_permissions()

    @action(methods=['get'], detail=False, url_path='current-user', permission_classes=[IsAuthenticated])
    def list_my_items(self, request, *args, **kwargs):
        if not request.GET._mutable:
            request.GET._mutable = True
        request.GET['user'] = request.user
        return super().list(request, *args, **kwargs)


class TransactionViewSet(BaseViewSet):
    queryset = models.Transaction.objects.all()
    serializer_class = serializers.TransactionSerializer
    filterset_class = filters.TransactionFilter
    http_method_names = ['get', 'post', 'head', 'options']

    @action(methods=['get'], detail=False, url_path='current-user', permission_classes=[IsAuthenticated])
    def list_my_items(self, request, *args, **kwargs):
        if not request.GET._mutable:
            request.GET._mutable = True
        request.GET['buyer'] = request.user
        return super().list(request, *args, **kwargs)
