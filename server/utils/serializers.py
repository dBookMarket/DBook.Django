import os
from collections import OrderedDict
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

    def get_absolute_uri(self, f_obj):
        try:
            return self.context['request'].build_absolute_uri(f_obj.url)
        except Exception as e:
            print(f'Fail to get absolute url, error:{e}')
            return ''

    def _validate_file(self, f_obj, allowed_extensions, max_size):
        if not allowed_extensions:
            allowed_extensions = ['jpg', 'png']
        if f_obj:
            file_name = f_obj.name
            extension = os.path.splitext(file_name)[1].replace('.', '')
            if extension.lower() not in allowed_extensions:
                raise serializers.ValidationError(
                    f'Invalid file type: {file_name}, must be one of {allowed_extensions}')

            if f_obj.size > max_size:
                raise serializers.ValidationError(f'The file size must be less than {max_size / (1024 * 1024)}Mb')


class CustomPKRelatedField(serializers.PrimaryKeyRelatedField):

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([
            (
                super(CustomPKRelatedField, self).to_representation(item),
                self.display_value(item)
            )
            for item in queryset
        ])
