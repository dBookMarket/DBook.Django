from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from utils.enums import UserType
from .models import User


class UserListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'account_addr', 'name', 'desc']


class UserRegistrySerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    account_addr = serializers.CharField(max_length=42, validators=[UniqueValidator(queryset=User.objects.all())])
    wallet_addr = serializers.CharField(required=False, max_length=42, allow_blank=True)
    type = serializers.ChoiceField(required=False, choices=UserType.choices())
    desc = serializers.CharField(required=False, max_length=1500)

    class Meta:
        model = User
        fields = ['username', 'account_addr', 'wallet_addr', 'type']


class UserLoginSerializer(serializers.ModelSerializer):
    account_addr = serializers.CharField(max_length=42, validators=[UniqueValidator(queryset=User.objects.all())])
    nonce = serializers.CharField(read_only=True)
    signature = serializers.CharField(required=True, max_length=520)

    class Meta:
        model = User
        fields = ['account_addr', 'nonce', 'signature']
