from django.db import models
from utils.models import BaseModel


class Notification(BaseModel):
    receiver = models.ForeignKey('users.User', to_field='id', related_name='notification_receiver',
                                 on_delete=models.SET_NULL, null=True, blank=True, default=None, verbose_name='接受者')
    title = models.CharField(blank=True, default='Notification', max_length=150, verbose_name='标题')
    message = models.TextField(verbose_name='内容')
    is_read = models.BooleanField(blank=True, default=False, verbose_name='已读')

    class Meta:
        ordering = ['-created_at', '-is_read']
        verbose_name = '消息通知'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.title}-{self.receiver.address}'
