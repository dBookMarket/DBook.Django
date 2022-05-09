from django.db import models
from utils.models import BaseModel
from accounts.models import User
from django.utils import timezone


class Trade(BaseModel):
    user = models.ForeignKey(to='accounts.User', to_field='account_addr', related_name='trade_user',
                             on_delete=models.CASCADE, verbose_name='卖家')
    issue = models.ForeignKey(to='books.Issue', to_field='id', related_name='trade_issue', on_delete=models.RESTRICT,
                              verbose_name='交易书籍')
    amount = models.IntegerField(blank=True, default=1, verbose_name='交易数量')
    price = models.FloatField(blank=True, default=0, verbose_name='发行价格')
    first_release = models.BooleanField(blank=True, default=False, verbose_name='是否首发')

    class Meta:
        ordering = ['id', 'user', 'issue']
        verbose_name = '书籍转卖'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.account_addr}-{self.issue.name}'


class Transaction(BaseModel):
    trade = models.ForeignKey(to='Trade', to_field='id', related_name='transaction_trade', on_delete=models.SET_NULL,
                              null=True, blank=True, default=None, verbose_name='挂单')
    issue = models.ForeignKey(to='books.Issue', to_field='id', related_name='transaction_issue',
                              on_delete=models.SET_NULL, null=True, blank=True, default=None, verbose_name='交易书籍')
    time = models.DateTimeField(blank=True, default=timezone.now, verbose_name='交易时间')
    amount = models.IntegerField(blank=True, default=1, verbose_name='交易数量')
    price = models.FloatField(blank=True, default=0, verbose_name='交易金额')
    seller = models.ForeignKey(to='accounts.User', to_field='account_addr', related_name='transaction_seller',
                               on_delete=models.SET_NULL, null=True, blank=True, default=None, verbose_name='卖家')
    buyer = models.ForeignKey(to='accounts.User', to_field='account_addr', related_name='transaction_buyer',
                              on_delete=models.CASCADE, verbose_name='买家')
    status = models.CharField(max_length=50, blank=True, default='pending', verbose_name='交易状态')
    hash = models.CharField(max_length=150, verbose_name='交易哈希值', unique=True, db_index=True)

    class Meta:
        ordering = ['id', 'trade']
        verbose_name = '交易记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.hash

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if force_insert:
            self.seller = self.trade.user
            self.issue = self.trade.issue
        super().save(force_insert, force_update, using, update_fields)
