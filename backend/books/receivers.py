from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Asset, Bookmark


# @receiver(post_save, sender=Asset)
# def save_asset(sender, instance, **kwargs):
#     try:
#         Bookmark.objects.get(user=instance.user, issue=instance.issue)
#     except Bookmark.DoesNotExist:
#         Bookmark.objects.create(user=instance.user, issue=instance.issue)

@receiver(post_save, sender=Asset)
def post_save_asset(sender, instance, **kwargs):
    if instance.amount == 0:
        instance.delete()
