from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from books.models import Asset, Issue, Book, Draft, Bookmark, Wishlist, Token
from django.db.transaction import atomic
from .file_service_connector import FileServiceConnector
from rest_framework.exceptions import ValidationError
from utils.helpers import ObjectPermHelper
from utils.enums import IssueStatus
from weasyprint import HTML
from django.conf import settings
import os
import uuid
from ebooklib import epub
from django.core.files import File
from books.models import Preview
from books.signals import sig_issue_new_book
from books.issue_handler import IssueHandler
from books.file_handler import FileHandlerFactory
import logging

logger = logging.getLogger(__name__)


def upload_pdf(obj_book):
    file_service_connector = FileServiceConnector()
    # revoke old task
    try:
        if obj_book.task_id:
            file_service_connector.revoke_task(obj_book.task_id)
    except Exception as e:
        logger.error(f'Exception when revoking file upload task: {e}, task id: {obj_book.task_id}')
        raise ValidationError(
            {'file': 'Update file failed because of the failure of revoking the old one.'}
        )
    # start a new task
    try:
        logger.info(f'pdf path -> {obj_book.file.path}')
        result = file_service_connector.upload_file(obj_book.file.path)
        if result:
            obj_book.task_id = result.task_id
            obj_book.save()
    except Exception as e:
        logger.error(f'Exception when calling upload_pdf: {e}')


def html_to_epub(obj_book: Book):
    if obj_book.draft:
        if not os.path.exists(settings.TEMPORARY_ROOT):
            os.makedirs(settings.TEMPORARY_ROOT)

        filename = f'{uuid.uuid4().hex}.epub'
        filepath = os.path.join(settings.TEMPORARY_ROOT, filename)

        book = epub.EpubBook()
        book.set_title(obj_book.draft.title)
        book.add_author(obj_book.author.name)
        book.set_cover('cover.jpg', obj_book.cover.open('rb').read())

        # cover = epub.EpubHtml(title='Cover', file_name='cover-page.xhtml')
        # cover.set_content('<p><img src="cover.jpg" alt="cover image"/></p>')

        # title = epub.EpubHtml(title='Title', file_name='title-page.xhtml')
        # title.set_content(f'<h1>{obj_book.draft.title}</h1>')

        content = epub.EpubHtml(title='Content', file_name='content-page.xhtml')
        content.set_content(obj_book.draft.content)

        # book.add_item(cover)
        # book.add_item(title)
        book.add_item(content)

        book.toc = (epub.Link('content-page.xhtml', 'Content', 'content'),)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        book.spine = ['cover', 'nav', content]
        epub.write_epub(filepath, book)

        try:
            with open(filepath, 'rb') as f:
                obj_book.file.save(f'{obj_book.draft.title}.epub', File(f))
        finally:
            os.remove(filepath)


def html_to_pdf(obj_book: Book):
    if obj_book.draft:
        filename = f'{uuid.uuid4().hex}.pdf'
        filepath = os.path.join(settings.TEMPORARY_ROOT, filename)
        HTML(string=obj_book.draft.content).write_pdf(filepath)
        try:
            with open(filepath, 'rb') as f:
                obj_book.file.save(f'{obj_book.draft.title}.pdf', File(f))
        finally:
            os.remove(filepath)


@receiver(post_save, sender=Draft)
def post_save_draft(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Draft, instance.author, instance)


@receiver(post_save, sender=Book)
def post_save_book(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Book, instance.author, instance)


@receiver(sig_issue_new_book, sender=Book)
@atomic
def issue_new_book(sender, instance, **kwargs):
    # convert draft to pdf if using draft
    html_to_epub(instance)

    # add preview
    # pdf_handler = PDFHandler(instance.file.path)
    f_handler = FileHandlerFactory(instance.type, instance.file.path)
    obj_preview, created = Preview.objects.get_or_create(book=instance)
    if not created and obj_preview.file:
        obj_preview.file.delete()
    pre_file = f_handler.get_preview_doc(from_page=obj_preview.start_page - 1,
                                         to_page=obj_preview.start_page + obj_preview.n_pages - 2)
    obj_preview.file = pre_file
    obj_preview.save()
    # update number of pages
    instance.n_pages = f_handler.get_pages()
    instance.save()
    # upload file to filecoin
    upload_pdf(instance)


@receiver(post_save, sender=Issue)
def post_save_issue(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Issue, instance.book.author, instance)

    if instance.status == IssueStatus.PRE_SALE.value:
        # set timer
        logger.info(f'Put issue {instance.id} into the queue')
        IssueHandler(instance).handle()


@receiver(pre_delete, sender=Issue)
def pre_delete_issue(sender, instance, **kwargs):
    if instance.status not in {IssueStatus.PRE_SALE.value, IssueStatus.UNSOLD.value}:
        raise ValidationError(f"It is not allowed to remove this issue because of the current status{instance.status}")


@receiver(post_save, sender=Asset)
def post_save_asset(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Asset, instance.user, instance)

        # add bookmark
        Bookmark.objects.update_or_create(user=instance.user, issue=instance.issue, defaults={'current_page': 1})

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


@receiver(post_save, sender=Token)
def post_save_token(sender, instance, **kwargs):
    if kwargs['created']:
        ObjectPermHelper.assign_perms(Token, instance.issue.book.author, instance)
