from .models import Book, EncryptionKey, Issue
from django.db.transaction import atomic
from utils.enums import CeleryTaskStatus, IssueStatus
from .file_service_connector import FileServiceConnector
from utils.redis_handler import IssueQueue
from books.issue_handler import IssueHandler
from datetime import timedelta
import pytz


def watch_celery_task():
    # todo how to update book info
    #   how to upload a book with one cid
    print('Dealing with celery tasks...')
    try:
        file_task_connector = FileServiceConnector()
        books = Book.objects.exclude(task_id='').exclude(status=CeleryTaskStatus.SUCCESS.value)
        for book in books:
            res = file_task_connector.get_async_result(book.task_id)
            current_status = res.status.lower()
            if current_status == CeleryTaskStatus.SUCCESS.value:
                data = res.get()
                with atomic():
                    book.status = current_status
                    book.cids = data['cids']
                    book.n_pages = data['n_pages']
                    book.save()
                    EncryptionKey.objects.update_or_create(
                        defaults={'private_key': data['private_key'], 'public_key': data['public_key'],
                                  'key_dict': data['key_dict']},
                        user=book.author
                    )
            else:
                if book.status != current_status:
                    book.status = current_status
                    book.save()

    except Exception as e:
        print(f'Exception when calling watch_celery_task: {e}')


def issue_timer():
    print('Check issue queue...')
    que = IssueQueue()
    issues = que.get_top()
    print(f'Current issues...{issues}')
    if issues:
        queryset = Issue.objects.filter(id__in=issues)
        for issue in queryset:
            with atomic():
                if issue.status == IssueStatus.PRE_SALE.value:
                    # update status
                    issue.status = IssueStatus.ON_SALE.value
                    issue.save()
                    # prepare for sale
                    IssueHandler(issue).handle()
                    # set timer for ending the sale
                    end_time = issue.published_at + timedelta(minutes=issue.duration)
                    utc_time = end_time.astimezone(pytz.UTC)
                    que.check_in(str(issue.id), utc_time.timestamp())
                elif issue.status == IssueStatus.ON_SALE.value:
                    # update status
                    if issue.n_circulations > 0:
                        issue.status = IssueStatus.OFF_SALE.value
                    else:
                        issue.status = IssueStatus.UNSOLD.value
                    issue.save()
                    # make it clean after sale
                    IssueHandler(issue).handle()
                    # quit queue
                    que.check_out()
                else:
                    que.check_out()
