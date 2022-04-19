from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True


class CurrentUserDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context['request'].user
