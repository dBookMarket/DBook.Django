from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Asset, Issue, EncryptionKey
from .signals import post_create_issue
from utils.enums import IssueStatus
from .file_service_connector import FileServiceConnector
from rest_framework.exceptions import ValidationError
from utils.helper import Helper


def upload_pdf(issue_obj):
    file_service_connector = FileServiceConnector()
    # revoke old task
    try:
        if issue_obj.task_id:
            file_service_connector.revoke_task(issue_obj.task_id)
    except Exception as e:
        print(f'Exception when revoking file upload task: {e}, task id: {issue_obj.task_id}')
        raise ValidationError(
            {'file': 'Update file failed because of the failure of revoking the old one.'}
        )
    try:
        # ek = EncryptionKey.objects.get(issue=issue_obj)
        # start a new task
        print(f'pdf path -> {issue_obj.file.path}')
        result = file_service_connector.upload_file(issue_obj.file.path)
        if result:
            issue_obj.task_id = result.task_id
            issue_obj.status = IssueStatus.UPLOADING.value
            issue_obj.save()
    except Exception as e:
        print(f'Exception when calling upload_pdf: {e}')
        issue_obj.status = IssueStatus.FAILURE.value
        issue_obj.save()


@receiver(post_save, sender=Asset)
def post_save_asset(sender, instance, **kwargs):
    if instance.amount == 0:
        instance.delete()


@receiver(post_create_issue, sender=Issue)
def post_create_issue(sender, instance, **kwargs):
    # send a celery task to upload file to nft.storage
    upload_pdf(instance)


@receiver(post_save, sender=Issue)
def post_save_issue(sender, instance, **kwargs):
    Helper().assign_perms(Issue, instance.publisher, instance)
