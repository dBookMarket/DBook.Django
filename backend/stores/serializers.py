from rest_framework import serializers
from utils.serializers import BaseSerializer, CurrentUserDefault
from rest_framework.validators import UniqueValidator
from books.models import Issue, Asset
from accounts.serializers import UserListingSerializer
from books.serializers import IssueListSerializer
from . import models
from django.db.models import Sum, Min


# No need to call file service when create a trade
class TradeSerializer(BaseSerializer):
    user = UserListingSerializer(required=False, default=CurrentUserDefault(), many=False)
    issue = serializers.PrimaryKeyRelatedField(queryset=Issue.objects.all(), many=False)
    amount = serializers.IntegerField(required=True)
    price = serializers.FloatField(required=True)
    first_release = serializers.BooleanField(required=False)

    issue_name = serializers.SerializerMethodField(read_only=True)
    issue_detail = serializers.SerializerMethodField(read_only=True)
    is_owned = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Trade
        fields = '__all__'

    def get_is_owned(self, obj):
        user = self.context['request'].user
        return user == obj.user

    def get_issue_name(self, obj):
        return obj.issue.name

    def get_issue_detail(self, obj):
        return IssueListSerializer(instance=obj.issue, many=False, context=self.context).data

    def validate(self, attrs):
        """
        validations:
            1, check if the amount is satisfied?
            2, check if the user has this book?
        """
        super().validate(attrs)
        user = self.context['request'].user
        issue = attrs.get('issue')
        amount = attrs.get('amount', 0)
        price = attrs.get('price')
        if issue:
            try:
                obj_asset = Asset.objects.get(user=user, issue=issue)
                all_trades = models.Trade.objects.filter(issue=issue)
                if price:
                    min_price = all_trades.aggregate(min_price=Min('price'))['min_price']
                    if min_price is None:
                        min_price = 20
                    if price < min_price:
                        raise serializers.ValidationError(
                            {'price': f'The price cannot below the minimum price({min_price}) of all trades'})
                n_sales = 0
                queryset = all_trades.filter(user=user)
                if self.instance:
                    queryset = queryset.exclude(id=self.instance.id)
                if queryset:
                    n_sales = queryset.aggregate(t_amount=Sum('amount'))['t_amount']
                if obj_asset.amount < (amount + n_sales):
                    raise serializers.ValidationError({'amount': 'The amount is beyond the number of books owned'})
            except Asset.DoesNotExist:
                raise serializers.ValidationError({'issue': 'The user does not have this book.'})
        return attrs


class TradeListingSerializer(TradeSerializer):
    class Meta(TradeSerializer.Meta):
        fields = ['user', 'issue_name']


class TransactionSerializer(BaseSerializer):
    trade = serializers.PrimaryKeyRelatedField(queryset=models.Trade.objects.all(), many=False)

    time = serializers.DateTimeField(required=False, input_formats=['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'],
                                     format='%Y-%m-%d %H:%M:%S')
    amount = serializers.IntegerField(required=True)
    price = serializers.FloatField(required=True)
    buyer = UserListingSerializer(required=False, default=CurrentUserDefault(), many=False)
    status = serializers.CharField(required=False, max_length=50, allow_blank=True)
    hash = serializers.CharField(required=True, max_length=150,
                                 validators=[UniqueValidator(queryset=models.Transaction.objects.all())])

    type = serializers.SerializerMethodField(read_only=True)
    seller = UserListingSerializer(read_only=True, many=False)
    issue = IssueListSerializer(read_only=True, many=False)

    class Meta:
        model = models.Transaction
        fields = '__all__'

    def get_type(self, obj):
        _type = 'unknown'
        user = self.context['request'].user
        if user == obj.buyer:
            _type = 'buy'
        elif user == obj.seller:
            _type = 'sale'
        return _type

    def validate(self, attrs):
        """
        validations:
            1, check if the amount is satisfied?
        """
        super().validate(attrs)
        trade = attrs.get('trade')
        amount = attrs.get('amount')
        if trade and amount and trade.amount < amount:
            raise serializers.ValidationError({'amount': 'The amount is beyond the remaining number'})
        return attrs

    def create(self, validated_data):
        obj_txn = self.Meta.model.objects.create(**validated_data)
        # 1, update trade
        obj_txn.trade.amount -= obj_txn.amount
        obj_txn.trade.save()
        # 2, update seller asset
        obj_asset = Asset.objects.get(user=obj_txn.trade.user, issue=obj_txn.trade.issue)
        obj_asset.amount -= obj_txn.amount
        obj_asset.save()
        # 3, update buyer asset
        try:
            obj_buyer_asset = Asset.objects.get(user=obj_txn.buyer, issue=obj_txn.trade.issue)
            obj_buyer_asset.amount += obj_txn.amount
            obj_buyer_asset.save()
        except Asset.DoesNotExist:
            Asset.objects.create(user=obj_txn.buyer, issue=obj_txn.trade.issue, amount=obj_txn.amount)
        return obj_txn
