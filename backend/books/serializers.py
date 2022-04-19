from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from . import models
from accounts.models import User
from accounts.serializers import UserListingSerializer
from utils.serializers import BaseSerializer, CurrentUserDefault
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from io import BytesIO
from .pdf_handler import PDFHandler
from django.db import transaction
from stores.models import Trade
from .nft_storage_handler import NFTStorageHandler
from django.core.files.base import File


class CategorySerializer(BaseSerializer):
    parent = serializers.PrimaryKeyRelatedField(required=False, queryset=models.Category.objects.all(), many=False,
                                                allow_null=True)
    name = serializers.CharField(max_length=150, allow_blank=False, allow_null=False)
    level = serializers.IntegerField(read_only=True)
    comment = serializers.CharField(required=False, max_length=200, allow_blank=True)

    class Meta:
        model = models.Category
        fields = '__all__'


class IssueListSerializer(BaseSerializer):
    class Meta:
        model = models.Issue
        fields = ['id', 'name', 'author_name', 'cover', 'n_pages']


class ContractSerializer(BaseSerializer):
    issue = serializers.PrimaryKeyRelatedField(queryset=models.Issue.objects.all(), many=False,
                                               validators=[UniqueValidator(queryset=models.Contract.objects.all())])
    address = serializers.CharField(required=True, max_length=150,
                                    validators=[UniqueValidator(queryset=models.Contract.objects.all())])
    token_amount = serializers.IntegerField(required=False)
    token_criteria = serializers.CharField(required=False, max_length=150, allow_blank=True)
    block_chain = serializers.CharField(required=False, max_length=150, allow_blank=True)
    token = serializers.CharField(required=False, max_length=150, allow_blank=True)

    class Meta:
        model = models.Contract
        fields = '__all__'

    def validate(self, attrs):
        super().validate(attrs)
        issue = attrs.get('issue')
        user = self.context['request'].user
        if issue.publisher != user:
            raise PermissionDenied(detail='You do not have permission to perform this action.')
        return attrs


class PreviewSerializer(BaseSerializer):
    issue = serializers.PrimaryKeyRelatedField(queryset=models.Issue.objects.all(), many=False,
                                               validators=[UniqueValidator(queryset=models.Preview.objects.all())])
    start_page = serializers.IntegerField(required=False)
    n_pages = serializers.IntegerField(required=False)

    file = serializers.FileField(required=False)

    class Meta:
        model = models.Preview
        fields = '__all__'


class IssueSerializer(BaseSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=models.Category.objects.all(), many=False)
    publisher = UserListingSerializer(required=False, many=False, default=CurrentUserDefault())

    author_name = serializers.CharField(required=True, max_length=150)
    author_desc = serializers.CharField(required=True, max_length=1500)
    # how about store into NFTStorge
    cover = serializers.ImageField(required=True)
    name = serializers.CharField(required=True, max_length=200)
    desc = serializers.CharField(required=True, max_length=1500)
    n_pages = serializers.IntegerField(read_only=True)

    number = serializers.CharField(required=False)
    amount = serializers.IntegerField()
    price = serializers.FloatField()
    ratio = serializers.FloatField(required=False)

    token = serializers.ReadOnlyField()
    token_url = serializers.ReadOnlyField()

    contract = ContractSerializer(read_only=True, many=False)
    preview = PreviewSerializer(read_only=True, many=False)

    class Meta:
        model = models.Issue
        fields = '__all__'

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)


class IssueBuildSerializer(IssueSerializer):
    publisher_name = serializers.CharField(required=True, max_length=150)
    publisher_desc = serializers.CharField(required=True, max_length=1500)
    file = serializers.FileField(required=True)

    class Meta:
        model = models.Issue
        fields = '__all__'

    def validate(self, attrs):
        """
        Validations:
            1, check if the file type is pdf?
        """
        super().validate(attrs)
        upload_file = attrs.get('file')
        if upload_file.content_type != 'application/pdf':
            raise serializers.ValidationError({'file': 'This field must be pdf file'})
        # # check file size
        # if upload_file.size > 5 * 1024 * 1024:  # 5Mb
        #     raise ValidationError({'file': 'The file size must be no more than 5Mb'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        file = validated_data.pop('file')
        publisher_name = validated_data.pop('publisher_name')
        publisher_desc = validated_data.pop('publisher_desc')
        file = BytesIO(file.read())
        pdf_handler = PDFHandler(file)
        n_pages = pdf_handler.get_pages()
        nft_token = pdf_handler.save_img()
        token_url = NFTStorageHandler.get_token_url(nft_token)
        obj_issue = self.Meta.model.objects.create(**validated_data, n_pages=n_pages, token=nft_token,
                                                   token_url=token_url)
        # 1, update publisher
        obj_issue.publisher.name = publisher_name
        obj_issue.publisher.desc = publisher_desc
        obj_issue.publisher.save()
        # 2, save preview
        # todo how to store previews?
        # current solution
        obj_preview = models.Preview.objects.create(issue=obj_issue)
        file = pdf_handler.get_preview_doc(from_page=obj_preview.start_page - 1,
                                           to_page=obj_preview.start_page + obj_preview.n_pages - 2)
        obj_preview.file = file
        obj_preview.save()
        # 4, save trade
        Trade.objects.create(issue=obj_issue, price=obj_issue.price, amount=obj_issue.amount,
                             user=obj_issue.publisher, first_release=True)
        # 5, asset
        models.Asset.objects.create(user=obj_issue.publisher, issue_id=obj_issue.id, amount=obj_issue.amount)
        return obj_issue


class BookmarkSerializer(BaseSerializer):
    user = serializers.PrimaryKeyRelatedField(required=False, default=CurrentUserDefault(), queryset=User.objects.all(),
                                              many=False)
    issue = serializers.PrimaryKeyRelatedField(queryset=models.Issue.objects.all(), many=False)
    current_page = serializers.IntegerField(required=False)

    class Meta:
        model = models.Bookmark
        fields = '__all__'
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
        try:
            asset = models.Asset.objects.get(user=user, issue=issue)
            if asset.amount < 1:
                raise serializers.ValidationError({'issue': 'Book not found'})
        except models.Asset.DoesNotExist:
            raise serializers.ValidationError({'issue': 'Book not found'})
        if current_page and (current_page > issue.n_pages or current_page < 1):
            raise serializers.ValidationError({'current_page': f'The range of page number is [1, {issue.n_pages}]'})
        return attrs


class BannerSerializer(BaseSerializer):
    img = serializers.ImageField(required=False, allow_null=True)
    name = serializers.CharField(max_length=150)
    desc = serializers.CharField(max_length=1500)
    redirect_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = models.Banner
        fields = '__all__'


class AssetSerializer(BaseSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)
    # issue = serializers.PrimaryKeyRelatedField(queryset=models.Issue.objects.all(), many=False)
    issue = IssueListSerializer(many=False)
    amount = serializers.IntegerField(required=False)
    file = serializers.HiddenField(default='')

    bookmark = serializers.DictField(read_only=True)

    class Meta:
        model = models.Asset
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=models.Asset.objects.all(),
                fields=['user', 'issue'],
                message='The user already has this book'
            )
        ]
