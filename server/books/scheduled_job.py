from .models import Issue, EncryptionKey
from django.db.transaction import atomic
from utils.enums import IssueStatus, CeleryTaskStatus
from .file_service_connector import FileServiceConnector


def watch_celery_task():
    # todo how to update book info
    #   how to upload a book with one cid
    try:
        file_task_connector = FileServiceConnector()
        issues = Issue.objects.filter(status=IssueStatus.UPLOADING.value)
        for issue in issues:
            if issue.task_id != '':
                res = file_task_connector.get_async_result(issue.task_id)
                if res.status == CeleryTaskStatus.SUCCESS.value:
                    data = res.get()
                    with atomic():
                        issue.status = IssueStatus.UPLOADED.value
                        issue.cids = data['cids']
                        # issue.nft_url = data['nft_url']
                        issue.n_pages = data['n_pages']
                        issue.save()
                        EncryptionKey.objects.update_or_create(
                            defaults={'private_key': data['private_key'], 'public_key': data['public_key'],
                                      'key_dict': data['key_dict']},
                            issue=issue
                        )
                elif res.status == CeleryTaskStatus.FAILURE.value:
                    issue.status = IssueStatus.FAILURE.value
                    issue.save()
    except Exception as e:
        print(f'Exception when calling watch_celery_task: {e}')
