from rest_framework import serializers
from utils.serializers import BaseSerializer
from users.serializers import UserRelatedField
from . import models


class NotificationSerializer(BaseSerializer):
    receiver = UserRelatedField(read_only=True)

    class Meta:
        model = models.Notification
        fields = '__all__'
