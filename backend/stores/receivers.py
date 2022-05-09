from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trade
from utils.helper import Helper


@receiver(post_save, sender=Trade)
def post_save_trade(sender, instance, **kwargs):
    Helper().assign_perms(Trade, instance.user, instance)
