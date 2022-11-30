from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trade, Benefit, Transaction
from utils.helpers import ObjectPermHelper
from stores.transaction_handler import TransactionHandler
from threading import Thread


@receiver(post_save, sender=Trade)
def post_save_trade(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Trade, instance.user, instance)
    # delete trade if quantity = 0
    if instance.quantity == 0:
        instance.delete()


@receiver(post_save, sender=Benefit)
def post_save_benefit(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Benefit, instance.user, instance)


@receiver(post_save, sender=Transaction)
def post_save_transaction(sender, instance, **kwargs):
    # TransactionHandler(instance).handle()
    t = Thread(target=TransactionHandler(instance).handle)
    t.daemon = True
    t.start()
