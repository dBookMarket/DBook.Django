from django.db.models.signals import post_save
from django.dispatch import receiver
from books.models import Asset, Issue, Book, Draft, Bookmark, Wishlist, Contract
from django.db.transaction import atomic
from .file_service_connector import FileServiceConnector
from rest_framework.exceptions import ValidationError
from utils.helpers import ObjectPermHelper
from weasyprint import HTML
from django.conf import settings
import os
import uuid
from django.core.files import File
from books.signals import sig_issue_new_book


def upload_pdf(obj_book):
    file_service_connector = FileServiceConnector()
    # revoke old task
    try:
        if obj_book.task_id:
            file_service_connector.revoke_task(obj_book.task_id)
    except Exception as e:
        print(f'Exception when revoking file upload task: {e}, task id: {obj_book.task_id}')
        raise ValidationError(
            {'file': 'Update file failed because of the failure of revoking the old one.'}
        )
    # start a new task
    try:
        print(f'pdf path -> {obj_book.file.path}')
        result = file_service_connector.upload_file(obj_book.file.path)
        if result:
            obj_book.task_id = result.task_id
            obj_book.save()
    except Exception as e:
        print(f'Exception when calling upload_pdf: {e}')


@receiver(post_save, sender=Draft)
def post_save_draft(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Draft, instance.author, instance)


@receiver(post_save, sender=Book)
def post_save_book(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Book, instance.author, instance)


@receiver(sig_issue_new_book, sender=Book)
def issue_new_book(sender, instance, **kwargs):
    # upload file to filecoin
    # convert draft to pdf if using draft
    if instance.draft:
        filename = f'{uuid.uuid4().hex}.pdf'
        filepath = os.path.join(settings.TEMPORARY_ROOT, filename)
        HTML(string=instance.draft.content).write_pdf(filepath)
        try:
            with open(filepath, 'rb') as f:
                instance.file.save(f'{instance.draft.title}.pdf', File(f))
        finally:
            os.remove(filepath)
    upload_pdf(instance)


@receiver(post_save, sender=Issue)
@atomic
def post_save_issue(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Issue, instance.book.author, instance)


@receiver(post_save, sender=Asset)
def post_save_asset(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Asset, instance.user, instance)

        # add bookmark
        Bookmark.objects.update_or_create(user=instance.user, book=instance.book, defaults={'current_page': 1})

    if instance.quantity == 0:
        instance.delete()


@receiver(post_save, sender=Bookmark)
def post_save_bookmark(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Bookmark, instance.user, instance)


@receiver(post_save, sender=Wishlist)
def post_save_wishlist(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Wishlist, instance.user, instance)


@receiver(post_save, sender=Contract)
def post_save_contract(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Contract, instance.book.author, instance)
