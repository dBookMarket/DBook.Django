from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .serializers import NotificationSerializer
import channels.layers
from asgiref.sync import async_to_sync
from utils.helpers import ObjectPermHelper


@receiver(post_save, sender=Notification)
def post_save_notification(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Notification, instance.receiver, instance)

    if not instance.is_read:
        layer = channels.layers.get_channel_layer()
        async_to_sync(layer.group_send)(
            f'notification_{instance.receiver.id}',
            {
                "type": "notify",
                "message": NotificationSerializer(instance, many=False).data
            }
        )