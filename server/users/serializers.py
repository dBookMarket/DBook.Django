from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from rest_framework.exceptions import PermissionDenied
from .models import User, Fans
from utils.serializers import CustomPKRelatedField
from django.contrib.auth.models import AnonymousUser
from django.db.models import Min, Max, Sum
from books.models import Issue, Asset


class UserRegistrySerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    address = serializers.CharField(max_length=42, validators=[UniqueValidator(queryset=User.objects.all())])
    desc = serializers.CharField(required=False, max_length=1500)

    class Meta:
        model = User
        fields = ['username', 'address', 'type']


class UserLoginSerializer(serializers.ModelSerializer):
    address = serializers.CharField(max_length=42, validators=[UniqueValidator(queryset=User.objects.all())])
    nonce = serializers.CharField(read_only=True)
    signature = serializers.CharField(required=True, max_length=520)

    class Meta:
        model = User
        fields = ['address', 'nonce', 'signature']


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, max_length=150)
    desc = serializers.CharField(required=False, max_length=1500)
    website_url = serializers.URLField(required=False)
    discord_url = serializers.URLField(required=False)
    avatar = serializers.ImageField(required=False, write_only=True)
    banner = serializers.ImageField(required=False, write_only=True)

    address = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)

    avatar_url = serializers.SerializerMethodField(read_only=True)
    banner_url = serializers.SerializerMethodField(read_only=True)

    statistic = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'address', 'name', 'desc', 'website_url', 'discord_url', 'avatar', 'banner', 'is_verified',
                  'avatar_url', 'banner_url', 'statistic']

    def get_absolute_uri(self, f_obj):
        request = self.context.get('request')
        try:
            return request.build_absolute_uri(f_obj) if f_obj else ''
        except Exception as e:
            print(f'Fail to get absolute url, error:{e}')
            return ''

    def get_avatar_url(self, obj):
        return self.get_absolute_uri(obj.avatar)

    def get_banner_url(self, obj):
        return self.get_absolute_uri(obj.banner)

    def get_statistic(self, obj):
        try:
            if obj.is_verified:
                queryset = Issue.objects.filter(book__author=obj)
                t_books = queryset.count()
                t_volume = 0
                sales = 0
                books = []
                for obj_issue in queryset:
                    t_volume += obj_issue.price * obj.quantity
                    sales += obj_issue.price * obj.n_circulations
                    books.append(obj_issue.book_id)
                tmp = queryset.annotate(lowest_price=Min('price'), highest_price=Max('price'))
                n_owners = Asset.objects.filter(book__in=books).count()
                return {
                    'total_volume': t_volume,
                    'lowest_price': tmp.lowest_price,
                    'highest_price': tmp.highest_price,
                    'total_books': t_books,
                    'sales': sales,
                    'n_owners': n_owners
                }
            return {}
        except AttributeError:
            return {}

    def validate(self, attrs):
        super().validate(attrs)

        user = self.context.get('request').user
        if user and self.instance and user.id != self.instance.id:
            raise PermissionDenied()

        return attrs


class UserListingSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ['id', 'address', 'name', 'desc', 'avatar_url']


class UserRelatedField(CustomPKRelatedField):

    def to_representation(self, value):
        try:
            obj = User.objects.get(id=value.pk)
            return UserListingSerializer(instance=obj, context=self.context).data
        except User.DoesNotExist:
            return {}


class FansSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False, required=False,
                                              default=serializers.CurrentUserDefault())
    # author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)
    author = UserRelatedField(queryset=User.objects.all(), many=False)

    class Meta:
        model = Fans
        fields = ['id', 'user', 'author']
        validators = [
            UniqueTogetherValidator(
                queryset=Fans.objects.all(),
                fields=['user', 'author'],
                message='You already subscribed this author.'
            )
        ]

    def validate(self, attrs):
        super().validate(attrs)
        user = self.context['request'].user
        author = attrs.get('author')
        if user and author and user.id == author.id:
            raise serializers.ValidationError('Sorry, you are not allowed to subscribe yourself.')
        return attrs
