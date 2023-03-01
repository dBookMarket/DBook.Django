from rest_framework import serializers
from . import models, signals
from users.models import User
from users.serializers import UserRelatedField
from stores.models import Trade
from utils.serializers import BaseSerializer, CustomPKRelatedField
from utils.enums import CeleryTaskStatus, BlockChainType
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from django.db.models import Max, Min, Sum
from django.contrib.auth.models import AnonymousUser
from django.forms.models import model_to_dict
from django.utils import timezone
import copy


class DraftSerializer(BaseSerializer):
    author = UserRelatedField(queryset=User.objects.all(), many=False, required=False,
                              default=serializers.CurrentUserDefault())
    title = serializers.CharField(max_length=150)
    content = serializers.CharField(max_length=1000000)

    class Meta:
        model = models.Draft
        fields = '__all__'


class BookSerializer(BaseSerializer):
    # author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False, required=False,
    #                                             default=serializers.CurrentUserDefault())
    author = UserRelatedField(queryset=User.objects.all(), many=False, required=False,
                              default=serializers.CurrentUserDefault())
    title = serializers.CharField(max_length=150)
    desc = serializers.CharField(max_length=1500)
    cover = serializers.ImageField(write_only=True)
    file = serializers.FileField(required=False, write_only=True)
    draft = serializers.PrimaryKeyRelatedField(required=False, write_only=True, queryset=models.Draft.objects.all(),
                                               many=False)

    cover_url = serializers.SerializerMethodField(read_only=True)

    status = serializers.ReadOnlyField()
    preview = serializers.SerializerMethodField(read_only=True)
    n_pages = serializers.ReadOnlyField()
    cid = serializers.ReadOnlyField()
    has_issued = serializers.SerializerMethodField(read_only=True)

    def get_has_issued(self, obj):
        try:
            models.Issue.objects.get(book=obj)
            return True
        except models.Issue.DoesNotExist:
            return False

    def get_preview(self, obj):
        try:
            instance = models.Preview.objects.get(book=obj)
            return PreviewListingSerializer(instance=instance, many=False, context=self.context).data
        except models.Preview.DoesNotExist:
            return {}

    def get_cover_url(self, obj):
        return self.get_absolute_uri(obj.cover)

    class Meta:
        model = models.Book
        exclude = ['task_id', 'type']

    def validate_file(self, value):
        self._validate_file(value, ['pdf', 'epub', 'txt'], 200 * 1024 * 1024)
        return value

    def validate_cover(self, value):
        self._validate_file(value, ['jpg', 'png'], 5 * 1024 * 1024)
        return value

    def validate_draft(self, value):
        user = self.context['request'].user
        if value:
            queryset = models.Draft.objects.filter(author=user).filter(id=value.id)
            if queryset.count() == 0:
                raise serializers.ValidationError('Sorry, you have no access to this draft.')
        return value

    def validate(self, attrs):
        super().validate(attrs)

        file = attrs.get('file')
        draft = attrs.get('draft')

        if not self.instance:
            if not file and not draft:
                raise serializers.ValidationError('No file or draft found')

        return attrs

    def create(self, validated_data):
        obj = super().create(validated_data)
        signals.sig_issue_new_book.send(sender=models.Book, instance=obj)
        return obj

    def update(self, instance, validated_data):
        old_obj = copy.deepcopy(instance)
        obj = super().update(instance, validated_data)

        if obj.draft:
            if (not old_obj.draft) or (old_obj.draft.id != obj.draft.id):
                signals.sig_issue_new_book.send(sender=models.Book, instance=obj)
        elif len(self.context['request'].FILES) != 0:
            signals.sig_issue_new_book.send(sender=self.Meta.model, instance=obj)

        return obj


class BookListingSerializer(BookSerializer):
    class Meta:
        model = models.Book
        fields = ['id', 'title', 'desc', 'cover_url', 'author', 'has_issued', 'status']


class TokenSerializer(BaseSerializer):
    issue = serializers.PrimaryKeyRelatedField(required=False, queryset=models.Issue.objects.all(), many=False,
                                               validators=[UniqueValidator(queryset=models.Token.objects.all())])
    contract_address = serializers.CharField(read_only=True)
    standard = serializers.CharField(required=False, max_length=150, allow_blank=True)
    block_chain = serializers.ChoiceField(required=True, choices=BlockChainType.choices())
    currency = serializers.CharField(required=False, max_length=150, allow_blank=True)

    class Meta:
        model = models.Token
        fields = '__all__'


class TokenNestSerializer(TokenSerializer):
    issue = serializers.PrimaryKeyRelatedField(required=False, queryset=models.Issue.objects.all(), many=False)

    class Meta(TokenSerializer.Meta):
        fields = '__all__'


class PreviewSerializer(BaseSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=models.Book.objects.all(), many=False,
                                              validators=[UniqueValidator(queryset=models.Preview.objects.all())])
    start_page = serializers.IntegerField(required=False)
    n_pages = serializers.IntegerField(required=False)

    file = serializers.FileField(required=False, write_only=True)

    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Preview
        fields = '__all__'

    def get_file_url(self, obj):
        return self.get_absolute_uri(obj.file)


class PreviewListingSerializer(PreviewSerializer):
    class Meta(PreviewSerializer.Meta):
        fields = ['file_url']


class BookRelatedField(CustomPKRelatedField):

    def to_representation(self, value):
        try:
            obj = models.Book.objects.get(id=value.pk)
            return BookSerializer(obj, context=self.context).data
        except models.Book.DoesNotExist:
            return {}


class IssueSerializer(BaseSerializer):
    # book = serializers.PrimaryKeyRelatedField(queryset=models.Book.objects.all(), many=False)
    book = BookRelatedField(required=True, queryset=models.Book.objects.all(), many=False,
                            validators=[UniqueValidator(queryset=models.Issue.objects.all())])
    quantity = serializers.IntegerField()
    price = serializers.FloatField()
    royalty = serializers.FloatField(required=False, min_value=0, max_value=100)
    buy_limit = serializers.IntegerField(required=False)
    published_at = serializers.DateTimeField()
    duration = serializers.IntegerField(min_value=1)

    status = serializers.ReadOnlyField()

    n_circulations = serializers.ReadOnlyField()

    # is_owned = serializers.SerializerMethodField(read_only=True)
    price_range = serializers.SerializerMethodField(read_only=True)
    # n_remains = serializers.SerializerMethodField(read_only=True)
    trade = serializers.SerializerMethodField(read_only=True)
    is_wished = serializers.SerializerMethodField(read_only=True)
    n_owners = serializers.SerializerMethodField(read_only=True)
    bookmark = serializers.SerializerMethodField(read_only=True)
    n_owned = serializers.SerializerMethodField(read_only=True)

    # token info
    token = TokenNestSerializer(required=True, many=False)

    class Meta:
        model = models.Issue
        fields = '__all__'

    def validate_royalty(self, value):
        if value == 0:
            raise serializers.ValidationError('This field must be larger than 0')
        return value

    def validate_token(self, value):
        token_issue = value.get('issue')
        if token_issue and self.instance and token_issue.id != self.instance.id:
            raise serializers.ValidationError('The token does not belong to this issue')
        return value

    def validate_book(self, value):
        if value.status != CeleryTaskStatus.SUCCESS.value:
            raise serializers.ValidationError(
                "It is not allowed to issue this book which has not been uploaded successfully.")
        user = self.context['request'].user
        queryset = models.Book.objects.filter(author=user).filter(id=value.id)
        if queryset.count() == 0:
            raise serializers.ValidationError('Sorry, this book is not yours!')
        return value

    def validate_published_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError('The value of published_at is invalid, should be after now.')
        return value

    def get_n_remains(self, obj):
        user = self.context['request'].user
        try:
            obj_asset = models.Asset.objects.get(user=user, issue=obj)
            n_sales = Trade.objects.filter(user=user, issue=obj).aggregate(t_amount=Sum('quantity'))['t_amount']
            if n_sales is None:
                n_sales = 0
            return obj_asset.quantity - n_sales
        except models.Asset.DoesNotExist:
            return 0

    def get_price_range(self, obj):
        _range = Trade.objects.filter(issue=obj).aggregate(min_price=Min('price'), max_price=Max('price'))
        if _range['min_price'] is None:
            _range['min_price'] = 0
        if _range['max_price'] is None:
            _range['max_price'] = _range['min_price']
        return _range

    def get_is_owned(self, obj):
        user = self.context['request'].user
        if isinstance(user, AnonymousUser):
            return False
        try:
            return models.Asset.objects.get(user=user, issue=obj).quantity > 0
        except models.Asset.DoesNotExist:
            return False

    def get_n_owned(self, obj):
        user = self.context['request'].user
        if isinstance(user, AnonymousUser):
            return 0
        try:
            n_assets = models.Asset.objects.get(user=user, issue=obj).quantity
            n_trades = Trade.objects.filter(user=user, issue=obj).aggregate(q=Sum('quantity'))['q']
            return n_assets - n_trades
        except models.Asset.DoesNotExist:
            return 0

    def get_n_owners(self, obj):
        return models.Asset.objects.filter(issue=obj).count()

    def get_is_wished(self, obj):
        user = self.context['request'].user
        if isinstance(user, AnonymousUser):
            return False
        try:
            models.Wishlist.objects.get(user=user, issue=obj)
            return True
        except models.Wishlist.DoesNotExist:
            return False

    def get_trade(self, obj):
        try:
            obj_trade = Trade.objects.get(issue=obj, first_release=True)
            return model_to_dict(obj_trade, fields=['id', 'quantity', 'price'])
        except Trade.DoesNotExist:
            return {}

    def get_bookmark(self, obj):
        _user = self.context['request'].user
        if isinstance(_user, AnonymousUser):
            return {}
        try:
            obj_bookmark = models.Bookmark.objects.get(user=_user, issue=obj)
            return BookmarkSerializer(instance=obj_bookmark, many=False).data
        except models.Bookmark.DoesNotExist:
            return {}

    def create(self, validated_data):
        token = validated_data.pop('token')
        obj_issue = super().create(validated_data)
        models.Token.objects.create(**token, issue=obj_issue)
        return obj_issue

    def update(self, instance, validated_data):
        token = validated_data.pop('token', None)
        obj_issue = super().update(instance, validated_data)
        if token:
            token['issue'] = obj_issue
            try:
                obj_token = models.Token.objects.get(issue=obj_issue)
                for key, value in token.items():
                    setattr(obj_token, key, value)
                obj_token.save()
            except models.Token.DoesNotExist:
                models.Token.objects.create(**token)
        return obj_issue


class IssueListingSerializer(IssueSerializer):
    class Meta(IssueSerializer.Meta):
        fields = ['id', 'book', 'price', 'quantity', 'n_circulations', 'published_at', 'status', 'token']


class IssueResaleSerializer(IssueSerializer):

    def validate(self, attrs):
        super().validate(attrs)
        published_at = attrs.get('published_at')
        if not published_at:
            raise serializers.ValidationError({'published_at': 'This field is required.'})
        return attrs


class BookmarkSerializer(BaseSerializer):
    # user = serializers.PrimaryKeyRelatedField(required=False, default=serializers.CurrentUserDefault(),
    #                                           queryset=User.objects.all(), many=False)
    issue = serializers.PrimaryKeyRelatedField(queryset=models.Issue.objects.all(), many=False)
    current_page = serializers.IntegerField(required=False)

    class Meta:
        model = models.Bookmark
        # fields = '__all__'
        exclude = ['user']
        validators = [
            UniqueTogetherValidator(
                queryset=models.Bookmark.objects.all(),
                fields=['user', 'issue'],
                message='This bookmark already exists'
            )
        ]

    def validate(self, attrs):
        """
        Validations:
        1, Check if the user has the book?
        2, Check if the current page is valid?
        """
        super().validate(attrs)
        issue = attrs.get('issue')
        current_page = attrs.get('current_page')
        user = self.context['request'].user
        if issue:
            try:
                asset = models.Asset.objects.get(user=user, issue=issue)
                if asset.quantity < 1:
                    raise serializers.ValidationError({'issue': 'Book not found'})
            except models.Asset.DoesNotExist:
                raise serializers.ValidationError({'issue': 'Book not found'})
        if current_page:
            # update operation
            if not issue and self.instance:
                issue = self.instance.issue
            if current_page > issue.book.n_pages or current_page < 1:
                raise serializers.ValidationError(
                    {'current_page': f'The range of page number is [1, {issue.book.n_pages}]'})
        return attrs


class AssetSerializer(BaseSerializer):
    quantity = serializers.IntegerField(required=False)
    issue = IssueListingSerializer(read_only=True)

    class Meta:
        model = models.Asset
        fields = ['id', 'issue', 'quantity']
        validators = [
            UniqueTogetherValidator(
                queryset=models.Asset.objects.all(),
                fields=['user', 'book'],
                message='The user already has this book'
            )
        ]


class IssueRelatedField(CustomPKRelatedField):

    def to_representation(self, value):
        try:
            obj = models.Issue.objects.get(id=value.pk)
            return IssueListingSerializer(instance=obj, context=self.context).data
        except models.Issue.DoesNotExist:
            return {}


class WishlistSerializer(BaseSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False, required=False,
                                              default=serializers.CurrentUserDefault())
    # issue = serializers.PrimaryKeyRelatedField(queryset=models.Issue.objects.all(), many=False)
    issue = IssueRelatedField(queryset=models.Issue.objects.all(), many=False)

    class Meta:
        model = models.Wishlist
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=models.Wishlist.objects.all(),
                fields=['user', 'issue'],
                message='You already collect it.'
            )
        ]


class AdvertiseSerializer(BaseSerializer):
    # issue = serializers.PrimaryKeyRelatedField(queryset=models.Issue.objects.all(), many=False)
    # show = serializers.BooleanField(required=False, default=True, write_only=True)

    issue = IssueSerializer(read_only=True)

    class Meta:
        model = models.Advertisement
        fields = ['id', 'issue']
