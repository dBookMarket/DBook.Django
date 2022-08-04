from django.db import models
from django.contrib.auth.models import AbstractUser
from utils.enums import UserType, SocialMediaType
from utils.helper import Helper
from utils.models import BaseModel


class User(AbstractUser):
    account_addr = models.CharField(max_length=42, unique=True, db_index=True, verbose_name='账户地址')
    nonce = models.CharField(blank=True, default=Helper.rand_nonce, max_length=512)
    wallet_addr = models.CharField(max_length=42, blank=True, default='', verbose_name='钱包地址')
    type = models.CharField(max_length=50, choices=UserType.choices(), default=UserType.READER.value,
                            verbose_name='用户类型')
    name = models.CharField(max_length=150, blank=True, default='', verbose_name='名称')
    desc = models.TextField(max_length=1500, blank=True, default='', verbose_name='用户描述')

    def __str__(self):
        return f'{self.account_addr}-{self.name}'

    @property
    def has_issue_perm(self):
        return self.has_perm('books.add_issue')


class SocialMedia(BaseModel):
    user = models.ForeignKey(to='User', to_field='account_addr', related_name='sma_user', on_delete=models.CASCADE,
                             verbose_name='用户')
    account_id = models.CharField(max_length=255, verbose_name='账户id')
    username = models.CharField(max_length=255, default='', verbose_name='账户名称')
    shared = models.BooleanField(blank=True, default=False, verbose_name='已分享')
    type = models.CharField(max_length=50, choices=SocialMediaType.choices(),
                            default=SocialMediaType.TWITTER.value, verbose_name='账号类型')

    def __str__(self):
        return f'{self.user.account_addr}-{self.account_id}-{self.type}'
