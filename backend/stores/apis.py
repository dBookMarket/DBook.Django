from . import models, serializers, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from utils.views import BaseViewSet


class TradeViewSet(BaseViewSet):
    queryset = models.Trade.objects.all()
    serializer_class = serializers.TradeSerializer
    filterset_class = filters.TradeFilter

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.first_release:
            raise ValidationError(detail='The first release cannot be removed')
        return super().destroy(request, *args, **kwargs)

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
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(Q(seller=request.user) | Q(buyer=request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
