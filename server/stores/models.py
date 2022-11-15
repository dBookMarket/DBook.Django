from django.db import models
from utils.models import BaseModel
from users.models import User
from utils.enums import Market


class Trade(BaseModel):
    user = models.ForeignKey(to='users.User', to_field='id', related_name='trade_user',
                             on_delete=models.CASCADE, verbose_name='卖家')
    book = models.ForeignKey(to='books.Book', to_field='id', related_name='trade_book', on_delete=models.CASCADE,
                             verbose_name='交易书籍')
    quantity = models.IntegerField(blank=True, default=1, verbose_name='交易数量')
    price = models.FloatField(blank=True, default=0, verbose_name='发行价格')
    first_release = models.BooleanField(blank=True, default=False, verbose_name='首发')

    class Meta:
        verbose_name = '书籍转卖'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.address}-{self.book.title}'


class Transaction(BaseModel):
    trade = models.ForeignKey(to='Trade', to_field='id', related_name='transaction_trade', on_delete=models.SET_NULL,
                              null=True, verbose_name='交易')
    # once the transaction exists, the book cannot be removed
    book = models.ForeignKey(to='books.Book', to_field='id', related_name='transaction_book',
                             on_delete=models.RESTRICT, default=None, verbose_name='交易书籍')
    quantity = models.IntegerField(blank=True, default=1, verbose_name='交易数量')
    price = models.FloatField(blank=True, default=0, verbose_name='交易金额')
    seller = models.ForeignKey(to='users.User', to_field='id', related_name='transaction_seller',
                               on_delete=models.RESTRICT, verbose_name='卖家')
    buyer = models.ForeignKey(to='users.User', to_field='id', related_name='transaction_buyer',
                              on_delete=models.RESTRICT, verbose_name='买家')
    status = models.CharField(max_length=50, blank=True, default='pending', verbose_name='交易状态')
    hash = models.CharField(max_length=150, verbose_name='交易哈希值', unique=True, db_index=True)
    source = models.IntegerField(choices=Market.choices())

    class Meta:
        verbose_name = '交易记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.hash

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if force_insert:
            self.seller = self.trade.user
            if self.trade.first_release:
                self.source = Market.FIRST_CLASS.value
            else:
                self.source = Market.SECOND_CLASS.value
        super().save(force_insert, force_update, using, update_fields)


class Benefit(BaseModel):
    user = models.ForeignKey(to='users.User', to_field='id', related_name='benefit_user',
                             on_delete=models.CASCADE, verbose_name='用户')
    transaction = models.ForeignKey(to='Transaction', to_field='id', related_name='benefit_transaction',
                                    on_delete=models.CASCADE, verbose_name='交易记录')
    amount = models.FloatField(verbose_name='收益')
    currency = models.CharField(max_length=50, verbose_name='币种')

    class Meta:
        verbose_name = '个人收益'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.name
