from rest_framework import serializers
from utils.serializers import BaseSerializer
from rest_framework.validators import UniqueValidator
from books.models import Asset, Book
from books.serializers import BookListingSerializer
from users.serializers import UserListingSerializer
from . import models
from django.db.models import Sum
from rest_framework.validators import UniqueTogetherValidator


# from django.db.transaction import atomic
# from django.conf import settings


# No need to call file service when create a trade
class TradeSerializer(BaseSerializer):
    user = UserListingSerializer(required=False, default=serializers.CurrentUserDefault(), many=False)
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), many=False)
    quantity = serializers.IntegerField(required=True)
    price = serializers.FloatField(required=True)
    is_owned = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Trade
        exclude = ['first_release']
        validators = [
            UniqueTogetherValidator(
                queryset=models.Trade.objects.all(),
                fields=['user', 'book'],
                message='This book already has been on sale'
            )
        ]

    def get_is_owned(self, obj):
        user = self.context['request'].user
        return user == obj.user

    def validate(self, attrs):
        """
        validations:
            1, check if the amount is satisfied?
            2, check if the user has this book?
        """
        super().validate(attrs)
        user = self.context['request'].user
        book = attrs.get('book')
        quantity = attrs.get('quantity', 0)
        if book:
            try:
                obj_asset = Asset.objects.get(user=user, book=book)
                all_trades = models.Trade.objects.filter(book=book)
                n_sales = 0
                queryset = all_trades.filter(user=user)
                if self.instance:
                    queryset = queryset.exclude(id=self.instance.id)
                if queryset:
                    n_sales = queryset.aggregate(t_amount=Sum('quantity'))['t_amount']
                if obj_asset.quantity < (quantity + n_sales):
                    raise serializers.ValidationError({'quantity': 'The quantity is beyond the number of books owned'})
            except Asset.DoesNotExist:
                raise serializers.ValidationError({'book': 'The user does not have this book.'})
        return attrs


class TradeListingSerializer(TradeSerializer):
    class Meta(TradeSerializer.Meta):
        fields = ['user', 'book']


class TransactionSerializer(BaseSerializer):
    trade = serializers.PrimaryKeyRelatedField(required=True, queryset=models.Trade.objects.all(), many=False)
    # book = serializers.PrimaryKeyRelatedField(required=False, queryset=Book.objects.all(), many=False)
    book = BookListingSerializer(many=False, read_only=True)
    quantity = serializers.IntegerField(required=True)
    price = serializers.FloatField(required=False)
    seller = UserListingSerializer(read_only=True, many=False)
    buyer = UserListingSerializer(required=False, default=serializers.CurrentUserDefault(), many=False)
    status = serializers.CharField(required=False, max_length=50, allow_blank=True)
    hash = serializers.CharField(required=True, max_length=150,
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
        if trade and quantity:
            if trade.quantity < quantity:
                raise serializers.ValidationError({'quantity': 'The quantity is beyond the remaining number'})
            if trade.first_release and trade.book.issue_book.buy_limit < quantity:
                raise serializers.ValidationError({
                    'quantity': f'The quantity is beyond the buy limit {trade.book.issue_book.buy_limit}'
                })
        buyer = attrs.get('buyer')
        if trade and buyer and trade.user.id == buyer.id:
            raise serializers.ValidationError({'buyer': 'You are not allowed to buy your own book'})
        return attrs

    # @atomic
    # def create(self, validated_data):
    #     obj_txn = self.Meta.model.objects.create(**validated_data)
    #     # 1, update trade
    #     obj_txn.trade.quantity -= obj_txn.quantity
    #     obj_txn.trade.save()
    #     # 2, update seller asset
    #     obj_asset = Asset.objects.get(user=obj_txn.trade.user, book=obj_txn.trade.book)
    #     obj_asset.quantity -= obj_txn.quantity
    #     obj_asset.save()
    #     # 3, update buyer asset
    #     try:
    #         obj_buyer_asset = Asset.objects.get(user=obj_txn.buyer, book=obj_txn.trade.book)
    #         obj_buyer_asset.quantity += obj_txn.quantity
    #         obj_buyer_asset.save()
    #     except Asset.DoesNotExist:
    #         Asset.objects.create(user=obj_txn.buyer, book=obj_txn.trade.book, quantity=obj_txn.quantity)
    #     # 4, update seller and author's benefit
    #     # first class market
    #     if obj_txn.trade.first_release:
    #         author_rate = 1 - settings.PLATFORM_ROYALTY
    #         amount = obj_txn.quantity * obj_txn.price * author_rate
    #         models.Benefit.objects.update_or_create(user=obj_txn.seller, transaction=obj_txn, defaults={
    #             'amount': amount,
    #             'currency': obj_txn.book.contract_book.token
    #         })
    #     else:
    #         # second class market
    #         author_rate = obj_txn.book.issue_book.royalty
    #         seller_rate = 1 - author_rate - settings.PLATFORM_ROYALTY
    #         t_amount = obj_txn.quantity * obj_txn.price
    #         author_amount = t_amount * author_rate
    #         seller_amount = t_amount * seller_rate
    #         models.Benefit.objects.update_or_create(user=obj_txn.book.author, transaction=obj_txn, defaults={
    #             'amount': author_amount,
    #             'currency': obj_txn.book.contract_book.token
    #         })
    #         models.Benefit.objects.update_or_create(user=obj_txn.seller, transaction=obj_txn, defaults={
    #             'amount': seller_amount,
    #             'currency': obj_txn.book.contract_book.token
    #         })
    #
    #     return obj_txn


class BenefitSerializer(BaseSerializer):
    class Meta:
        model = models.Benefit
        fields = '__all__'
