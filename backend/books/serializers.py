import os.path

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from . import models, signals
from accounts.models import User
from accounts.serializers import UserListingSerializer
from utils.serializers import BaseSerializer, CurrentUserDefault
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from secure.encryption_handler import EncryptionHandler
from django.conf import settings


class CategorySerializer(BaseSerializer):
    parent = serializers.PrimaryKeyRelatedField(required=False, queryset=models.Category.objects.all(), many=False,
                                                allow_null=True)
    name = serializers.CharField(max_length=150, allow_blank=False, allow_null=False)
    level = serializers.IntegerField(read_only=True)
    comment = serializers.CharField(required=False, max_length=200, allow_blank=True)

    class Meta:
        model = models.Category
        fields = '__all__'


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
        # update operation
        if not issue and self.instance:
            issue = self.instance.issue
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

    cover = serializers.ImageField(required=True, write_only=True)
    name = serializers.CharField(required=True, max_length=200)
    desc = serializers.CharField(required=True, max_length=1500)
    n_pages = serializers.IntegerField(read_only=True)

    number = serializers.CharField(required=False)
    amount = serializers.IntegerField()
    price = serializers.FloatField()
    ratio = serializers.FloatField(required=False)

    publisher_name = serializers.CharField(required=True, max_length=150, write_only=True)
    publisher_desc = serializers.CharField(required=True, max_length=1500, write_only=True)
    file = serializers.FileField(required=True, write_only=True)

    cid = serializers.ReadOnlyField()
    nft_url = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    n_owners = serializers.ReadOnlyField()
    n_circulations = serializers.ReadOnlyField()

    is_owned = serializers.SerializerMethodField(read_only=True)

    contract = ContractSerializer(read_only=True, many=False)
    preview = PreviewSerializer(read_only=True, many=False)

    cover_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Issue
        # fields = '__all__'
        exclude = ['task_id']

    def get_is_owned(self, obj):
        user = self.context['request'].user
        try:
            return models.Asset.objects.get(user=user, issue=obj).amount > 0
        except models.Asset.DoesNotExist:
            return False

    def get_cover_url(self, obj):
        request = self.context.get('request')
        if request and obj.cover:
            return request.build_absolute_uri(obj.cover.url)
        return ''

    def validate(self, attrs):
        """
        Validations:
            1, check if the file type is pdf?
        """
        super().validate(attrs)
        upload_file = attrs.get('file')
        if upload_file:
            if upload_file.content_type != 'application/pdf':
                raise serializers.ValidationError({'file': 'This field must be pdf file'})
            # check file size
            if upload_file.size > 60 * 1024 * 1024:  # 60Mb
                raise serializers.ValidationError({'file': 'The file size must be no more than 60Mb'})
        return attrs

    def create_encryption_key(self, issue):
        enc_handler = EncryptionHandler()
        sk_file = os.path.join(settings.PRIVATE_KEY_DIR, f'issue-{issue.id}-sk.stk')
        pk_file = os.path.join(settings.PUBLIC_KEY_DIR, f'issue-{issue.id}-pk.pck')
        dict_file = os.path.join(settings.KEY_DICT_DIR, f'issue-{issue.id}-kd.dict')
        enc_handler.generate_private_key(sk_file)
        enc_handler.generate_public_key(pk_file, sk_file)
        enc_handler.generate_key_dict(dict_file, sk_file)
        models.EncryptionKey.objects.update_or_create(
            defaults={'private_key': sk_file, 'public_key': pk_file, 'key_dict': dict_file},
            issue=issue
        )

    def create(self, validated_data):
        publisher_name = validated_data.pop('publisher_name')
        publisher_desc = validated_data.pop('publisher_desc')
        obj_issue = self.Meta.model.objects.create(**validated_data)
        # add perm
        self.assign_perms(obj_issue.publisher, obj_issue)
        # update publisher
        obj_issue.publisher.name = publisher_name
        obj_issue.publisher.desc = publisher_desc
        obj_issue.publisher.save()
        # add encryption key
        self.create_encryption_key(obj_issue)
        # send signal
        signals.post_create_issue.send(sender=self.Meta.model, instance=obj_issue)
        return obj_issue

    def update(self, instance, validated_data):
        publisher_name = validated_data.pop('publisher_name', None)
        publisher_desc = validated_data.pop('publisher_desc', None)

        obj = super().update(instance, validated_data)
        # update publisher
        if publisher_name:
            obj.publisher.name = publisher_name
        if publisher_desc:
            obj.publisher.desc = publisher_desc
        if publisher_name or publisher_desc:
            obj.publisher.save()

        if len(self.context['request'].FILES) != 0:
            self.create_encryption_key(obj)
            # send signal
            signals.post_create_issue.send(sender=self.Meta.model, instance=obj)
        return obj


class IssueListSerializer(IssueSerializer):
    class Meta:
        model = models.Issue
        fields = ['id', 'name', 'author_name', 'cover_url', 'n_pages', 'status']


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
        if issue:
            try:
                asset = models.Asset.objects.get(user=user, issue=issue)
                if asset.amount < 1:
                    raise serializers.ValidationError({'issue': 'Book not found'})
            except models.Asset.DoesNotExist:
                raise serializers.ValidationError({'issue': 'Book not found'})
        if current_page:
            # update operation
            if not issue and self.instance:
                issue = self.instance.issue
            if current_page > issue.n_pages or current_page < 1:
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
