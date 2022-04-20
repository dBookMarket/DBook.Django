from rest_framework import serializers
from guardian.shortcuts import assign_perm


class BaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = None
        abstract = True

    def assign_perms(self, user, instance):
        if self.Meta.model is not None:
            model_name = self.Meta.model._meta.model_name
            assign_perm(f'change_{model_name}', user, instance)
            assign_perm(f'delete_{model_name}', user, instance)


class CurrentUserDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context['request'].user
