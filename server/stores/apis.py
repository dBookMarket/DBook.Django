from . import models, serializers, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions, IsAuthenticatedOrReadOnly
from authorities.permissions import ObjectPermissionsOrReadOnly
from rest_framework.response import Response
from django.db.models import Q, Sum
from utils.views import BaseViewSet


class TradeViewSet(BaseViewSet):
    permission_classes = [ObjectPermissionsOrReadOnly]
    queryset = models.Trade.objects.all()
    serializer_class = serializers.TradeSerializer
    filterset_class = filters.TradeFilter

    # def get_permissions(self):
    #     if self.action in {'update', 'destroy', 'partial_update'}:
    #         self.permission_classes = [DjangoObjectPermissions]
    #     return super().get_permissions()

    @action(methods=['get'], detail=False, url_path='current', permission_classes=[IsAuthenticated])
    def list_current(self, request, *args, **kwargs):
        if not request.GET._mutable:
            request.GET._mutable = True
        request.GET['user'] = request.user
        return super().list(request, *args, **kwargs)


class TransactionViewSet(BaseViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = models.Transaction.objects.all()
    serializer_class = serializers.TransactionSerializer
    filterset_class = filters.TransactionFilter
    http_method_names = ['get', 'post']

    @action(methods=['get'], detail=False, url_path='current', permission_classes=[IsAuthenticated])
    def list_current(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(Q(seller=request.user) | Q(buyer=request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path='trend')
    def trend(self, request, *args, **kwargs):
        """
        Count the sales of each day
        """
        queryset = self.filter_queryset(self.get_queryset())
        _queryset = queryset.values('created_at__date').annotate(q=Sum('quantity')).values('created_at__date',
                                                                                           'q').order_by(
            'created_at__date')
        dates = []
        quantities = []
        for obj in _queryset:
            dates.append(obj.created_at__date.strftime('%Y-%m-%d'))
            quantities.append(obj.q)
        return Response({
            'dates': dates,
            'quantities': quantities
        })


class BenefitViewSet(BaseViewSet):
    queryset = models.Benefit.objects.all()
    serializer_class = serializers.BenefitSerializer
    http_method_names = ['get']

    @action(methods=['get'], detail=False, url_path='total')
    def total(self, request, *args, **kwargs):
        """
        return the user's total benefit
        """
        queryset = self.filter_queryset(self.get_queryset())
        t_benefits = queryset.values('currency').annotate(t_amount=Sum('amount')).values('currency', 't_amount')
        res = [{'currency': _obj.currency, 'amount': _obj.t_amount} for _obj in t_benefits]
        return Response(res)
