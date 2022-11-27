from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trade, Benefit, Transaction
from books.models import Asset
from utils.helpers import ObjectPermHelper
from django.conf import settings
from django.db.transaction import atomic


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
@atomic
def post_save_transaction(sender, instance, **kwargs):
    # todo need to call smart contract to send a transaction
    if instance.status == 'success':
        # 0, update issue
        if instance.trade.first_release:
            instance.issue.n_circulations += instance.quantity
            instance.issue.save()
        # 1, update trade
        instance.trade.quantity -= instance.quantity
        instance.trade.save()
        # 2, update seller asset
        if not instance.trade.first_release:
            obj_asset = Asset.objects.get(user=instance.trade.user, issue=instance.trade.issue)
            obj_asset.quantity -= instance.quantity
            obj_asset.save()
        # 3, update buyer asset
        try:
            obj_buyer_asset = Asset.objects.get(user=instance.buyer, issue=instance.trade.issue)
            obj_buyer_asset.quantity += instance.quantity
            obj_buyer_asset.save()
        except Asset.DoesNotExist:
            Asset.objects.create(user=instance.buyer, issue=instance.trade.issue, quantity=instance.quantity)
        # 4, update seller and author's benefit
        # first class market
        if instance.trade.first_release:
            author_rate = 1 - settings.PLATFORM_ROYALTY
            amount = instance.quantity * instance.price * author_rate
            Benefit.objects.update_or_create(user=instance.seller, transaction=instance, defaults={
                'amount': amount,
                'currency': instance.issue.token_issue.currency
            })
        else:
            # second class market
            author_rate = instance.issue.royalty
            seller_rate = 1 - author_rate - settings.PLATFORM_ROYALTY
            t_amount = instance.quantity * instance.price
            author_amount = t_amount * author_rate
            seller_amount = t_amount * seller_rate
            Benefit.objects.update_or_create(user=instance.issue.book.author, transaction=instance, defaults={
                'amount': author_amount,
                'currency': instance.issue.token_issue.currency
            })
            Benefit.objects.update_or_create(user=instance.seller, transaction=instance, defaults={
                'amount': seller_amount,
                'currency': instance.issue.token_issue.currency
            })
