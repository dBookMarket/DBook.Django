import uuid
# from random import random
from web3.auto import w3
from web3 import Web3
from eth_account.messages import encode_defunct
import time
from guardian.shortcuts import assign_perm, remove_perm
from guardian.core import ObjectPermissionChecker
from django.contrib.auth.models import Group, Permission


class Helper:

    @staticmethod
    def rand_nonce(digits: int = 7) -> str:
        # return str(int(random() * 10 ** digits))
        return Web3.toHex(Web3.keccak(text=str(int(time.time() * 10 ** digits)))).strip('0x')

    @staticmethod
    def rand_username() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def eth_recover(message: str, signature: str) -> str:
        msg_hash = encode_defunct(text=message)
        signer = w3.eth.account.recover_message(msg_hash, signature=signature)
        return signer

    @staticmethod
    def equal(str1: str, str2: str):
        return str(str1).lower() == str(str2).lower()

    @staticmethod
    def assign_perms(model, user, instance):
        """
        assign object permission
        :param model: django model
        :param user: user instance
        :param instance: object assigned for
        :return:
        """
        try:
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            change_perm = Permission.objects.get(codename=f'change_{model_name}')
            delete_perm = Permission.objects.get(codename=f'delete_{model_name}')
            # get or create a group which includes the model-level permissions
            group, created = Group.objects.get_or_create(name=f'{app_label}_{model_name}_owner')
            if created:
                group.permissions.set([change_perm, delete_perm])
            user.groups.add(group)
            # assign object permissions
            checker = ObjectPermissionChecker(user)
            if not checker.has_perm(change_perm.codename, instance):
                print(f'{user.address} does not have perm change {model_name}')
                assign_perm(change_perm, user, instance)
            if not checker.has_perm(delete_perm.codename, instance):
                print(f'{user.address} does not have perm delete {model_name}')
                assign_perm(delete_perm, user, instance)
        except Exception as e:
            print(f'Exception when calling Helper->assign_perms: {e}')


class ObjectPermHelper:

    @classmethod
    def assign_perms(cls, model_cls, user, obj):
        cls.assign_change_perm(model_cls, user, obj)
        cls.assign_delete_perm(model_cls, user, obj)

    @classmethod
    def assign_change_perm(cls, model_cls, user, obj):
        cls.__assign_perm(model_cls, user, obj, 'change')

    @classmethod
    def assign_delete_perm(cls, model_cls, user, obj):
        cls.__assign_perm(model_cls, user, obj, 'delete')

    @classmethod
    def assign_view_perm(cls, model_cls, user, obj):
        cls.__assign_perm(model_cls, user, obj, 'view')

    @classmethod
    def __assign_perm(cls, model_cls, user, obj, action):
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name
        perm = f"{app_label}.{action}_{model_name}"
        if not user.has_perm(perm, obj):
            assign_perm(perm, user, obj)

    @classmethod
    def assign_custom_perm(cls, model_cls, code, user, obj):
        app_label = model_cls._meta.app_label
        perm = f'{app_label}.{code}'
        if not user.has_perm(perm, obj):
            assign_perm(perm, user, obj)

    @classmethod
    def __remove_perm(cls, model_cls, user, obj, action):
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name
        perm = f"{app_label}.{action}_{model_name}"
        if user.has_perm(perm, obj):
            remove_perm(perm, user, obj)

    @classmethod
    def remove_view_perm(cls, model_cls, user, obj):
        cls.__remove_perm(model_cls, user, obj, 'view')

    @classmethod
    def remove_change_perm(cls, model_cls, user, obj):
        cls.__remove_perm(model_cls, user, obj, 'change')

    @classmethod
    def remove_delete_perm(cls, model_cls, user, obj):
        cls.__remove_perm(model_cls, user, obj, 'delete')
