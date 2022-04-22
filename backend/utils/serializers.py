from rest_framework import serializers
from guardian.shortcuts import assign_perm
from django.contrib.auth.models import Group, Permission


class BaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = None
        abstract = True

    def assign_perms(self, user, instance):
        if self.Meta.model is not None:
            app_label = self.Meta.model._meta.app_label
            model_name = self.Meta.model._meta.model_name
            change_perm = Permission.objects.get(codename=f'change_{model_name}')
            delete_perm = Permission.objects.get(codename=f'delete_{model_name}')
            # get or create a group which includes the model-level permissions
            group, created = Group.objects.get_or_create(name=f'{app_label}_{model_name}_owner')
            if created:
                group.permissions.set([change_perm, delete_perm])
            user.groups.add(group)
            # assign object permissions
            assign_perm(change_perm, user, instance)
            assign_perm(delete_perm, user, instance)


class CurrentUserDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context['request'].user
