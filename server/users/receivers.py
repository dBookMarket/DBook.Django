from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import Fans
from utils.helpers import ObjectPermHelper


@receiver(post_save, sender=Fans)
def post_save_fans(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Fans, instance.user, instance)
