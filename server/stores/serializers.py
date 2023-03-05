from rest_framework import serializers
from utils.serializers import BaseSerializer
from utils.enums import IssueStatus, TransactionStatus
from rest_framework.validators import UniqueValidator
from books.models import Asset, Issue
from books.serializers import IssueListingSerializer, IssueRelatedField
from users.models import User
from users.serializers import UserListingSerializer, UserRelatedField
from . import models
from django.db.models import Sum
from rest_framework.validators import UniqueTogetherValidator


# No need to call file service when create a trade
class TradeSerializer(BaseSerializer):
    user = UserRelatedField(required=False, queryset=User.objects.all(), default=serializers.CurrentUserDefault(),
                            many=False)
    issue = IssueRelatedField(queryset=Issue.objects.all(), many=False)
    quantity = serializers.IntegerField(required=True)
    price = serializers.FloatField(required=True)
    is_owned = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Trade
        exclude = ['first_release']
        validators = [
            UniqueTogetherValidator(
                queryset=models.Trade.objects.all(),
                fields=['user', 'issue'],
                message='This book already has been on sale'
            )
        ]

    def get_is_owned(self, obj):
        user = self.context['request'].user
        return user == obj.user

    def validate_issue(self, value):
        if value.status != IssueStatus.OFF_SALE.value:
            raise serializers.ValidationError(
                'You are not allowed to trade this book because the first release is still on sale.')
        return value

    def validate(self, attrs):
        """
        validations:
            1, check if the amount is satisfied?
            2, check if the user has this book?
        """
        super().validate(attrs)
        user = self.context['request'].user
        issue = attrs.get('issue')
        quantity = attrs.get('quantity', 0)
        if issue:
            try:
                obj_asset = Asset.objects.get(user=user, issue=issue)
                all_trades = models.Trade.objects.filter(issue=issue)
                n_sales = 0
                queryset = all_trades.filter(user=user)
                if self.instance:
                    queryset = queryset.exclude(id=self.instance.id)
                if queryset:
                    n_sales = queryset.aggregate(t_quantity=Sum('quantity'))['t_quantity']
                    if n_sales is None:
                        n_sales = 0
                if obj_asset.quantity < (quantity + n_sales):
                    raise serializers.ValidationError({'quantity': 'The quantity is beyond the number of books owned'})
            except Asset.DoesNotExist:
                raise serializers.ValidationError({'book': 'Please make sure you have this book before trading'})
        return attrs


class TradeListingSerializer(TradeSerializer):
    class Meta:
        model = models.Trade
        fields = ['user', 'issue']


class TransactionSerializer(BaseSerializer):
    trade = serializers.PrimaryKeyRelatedField(required=True, queryset=models.Trade.objects.all(), many=False)
    # book = serializers.PrimaryKeyRelatedField(required=False, queryset=Book.objects.all(), many=False)
    # book = BookListingSerializer(many=False, read_only=True)
    issue = IssueListingSerializer(many=False, read_only=True)
    quantity = serializers.IntegerField(required=True)
    price = serializers.FloatField(required=False)
    seller = UserListingSerializer(read_only=True, many=False)
    buyer = UserRelatedField(required=False, queryset=User.objects.all(), default=serializers.CurrentUserDefault(),
                             many=False)
    status = serializers.CharField(required=False, max_length=50, allow_blank=True)
    hash = serializers.CharField(required=False, max_length=150,
                                 validators=[UniqueValidator(queryset=models.Transaction.objects.all())])

    source = serializers.IntegerField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)

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
            1, check if the quantity is satisfied?
        """
        super().validate(attrs)
        trade = attrs.get('trade')
        quantity = attrs.get('quantity')
        _hash = attrs.get('hash')
        _status = attrs.get('status')
        if trade and quantity:
            if not trade.first_release:
                if not _hash:
                    raise serializers.ValidationError({'hash': 'This field is required'})
                allowed_status = {TransactionStatus.SUCCESS.value, TransactionStatus.FAILURE.value}
                if _status not in allowed_status:
                    raise serializers.ValidationError({
                        'status': f'This field is invalid, must be one of {allowed_status}'
                    })
            # todo need lock?
            if trade.quantity < quantity:
                raise serializers.ValidationError({'quantity': 'The quantity is beyond the remaining number'})
            if trade.first_release:
                user = self.context['request'].user
                _except_ids = [self.instance.id] if self.instance else []
                n_owns = models.Transaction.objects.filter(buyer=user, issue=trade.issue,
                                                           status__in={
                                                               TransactionStatus.PENDING.value,
                                                               TransactionStatus.SUCCESS.value
                                                           }).exclude(id__in=_except_ids).aggregate(
                    t=Sum('quantity'))['t']
                if n_owns is None:
                    n_owns = 0
                if trade.issue.buy_limit < n_owns + quantity:
                    raise serializers.ValidationError({
                        'quantity': f'The quantity is beyond the buy limit({trade.issue.buy_limit})'
                    })
        buyer = attrs.get('buyer')
        if trade and buyer and trade.user.id == buyer.id:
            raise serializers.ValidationError({'buyer': 'You are not allowed to buy your own book'})
        return attrs


class BenefitSerializer(BaseSerializer):
    class Meta:
        model = models.Benefit
        fields = '__all__'
