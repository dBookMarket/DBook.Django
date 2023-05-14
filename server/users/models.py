from django.db import models
from django.contrib.auth.models import AbstractUser
from utils.enums import SocialMediaType
from utils.helpers import Helper
from utils.models import BaseModel


class User(AbstractUser):
    address = models.CharField(max_length=42, unique=True, verbose_name='账户地址')
    nonce = models.CharField(blank=True, default=Helper.rand_nonce, max_length=512)
    name = models.CharField(max_length=150, blank=True, default='', verbose_name='名称')
    desc = models.TextField(max_length=1500, blank=True, default='', verbose_name='用户描述')
    website_url = models.URLField(blank=True, default='', verbose_name='个人网站URL')
    discord_url = models.URLField(blank=True, default='', verbose_name='discord主页')
    twitter_url = models.URLField(blank=True, default='', verbose_name='twitter主页')
    avatar = models.ImageField(blank=True, default=None, upload_to='avatar', verbose_name='头像')
    banner = models.ImageField(blank=True, default=None, upload_to='banner', verbose_name='banner')
    is_verified = models.BooleanField(blank=True, default=False, verbose_name='已认证(twitter)')

    class Meta:
        ordering = ['id']
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.address}-{self.name}'


class Account(BaseModel):
    user = models.ForeignKey(to='User', to_field='id', related_name='sma_user', on_delete=models.CASCADE,
                             verbose_name='用户')
    account_id = models.CharField(max_length=255, verbose_name='账户id')
    username = models.CharField(max_length=255, default='', verbose_name='账户名称')
    shared = models.BooleanField(blank=True, default=False, verbose_name='已分享')
    type = models.CharField(max_length=50, choices=SocialMediaType.choices(),
                            default=SocialMediaType.TWITTER.value, verbose_name='账号类型')

    class Meta:
        ordering = ['id']
        verbose_name = '账户'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'type']

    def __str__(self):
        return f'{self.user.address}-{self.account_id}-{self.type}'


class Fans(BaseModel):
    user = models.ForeignKey(to='User', to_field='id', related_name='fans_user', on_delete=models.CASCADE,
                             verbose_name='用户')
    author = models.ForeignKey(to='User', to_field='id', related_name='fans_author', on_delete=models.CASCADE,
                               verbose_name='作者')

    class Meta:
        ordering = ['id']
        verbose_name = '粉丝'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.name}-{self.author.name}'
