from rest_framework import viewsets
from . import models, serializers
from authorities.permissions import ObjectPermissionsOrReadOnly


class TradeViewSet(viewsets.ModelViewSet):
    permission_classes = [ObjectPermissionsOrReadOnly]
    queryset = models.Trade.objects.all()
    serializer_class = serializers.TradeSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = models.Transaction.objects.all()
    serializer_class = serializers.TransactionSerializer

    http_method_names = ['get', 'post', 'head', 'options']
