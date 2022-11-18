from .models import Book, EncryptionKey
from django.db.transaction import atomic
from utils.enums import CeleryTaskStatus
from .file_service_connector import FileServiceConnector


def watch_celery_task():
    # todo how to update book info
    #   how to upload a book with one cid
    try:
        file_task_connector = FileServiceConnector()
        books = Book.objects.filter(status=CeleryTaskStatus.STARTED.value)
        for book in books:
            if book.task_id != '':
                res = file_task_connector.get_async_result(book.task_id)
                current_status = res.status.lower()
                if current_status == CeleryTaskStatus.SUCCESS.value:
                    data = res.get()
                    with atomic():
                        book.status = current_status
                        book.cids = data['cids']
                        # issue.nft_url = data['nft_url']
                        book.n_pages = data['n_pages']
                        book.save()
                        EncryptionKey.objects.update_or_create(
                            defaults={'private_key': data['private_key'], 'public_key': data['public_key'],
                                      'key_dict': data['key_dict']},
                            user=book.author
                        )
                elif current_status == CeleryTaskStatus.FAILURE.value:
                    book.status = current_status
                    book.save()
    except Exception as e:
        print(f'Exception when calling watch_celery_task: {e}')
