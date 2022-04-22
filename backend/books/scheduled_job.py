from .models import Issue
from utils.enums import FileUploadStatus, CeleryTaskStatus
from .file_service_connector import FileServiceConnector


def watch_celery_task():
    try:
        file_task_connector = FileServiceConnector()
        issues = Issue.objects.filter(status=FileUploadStatus.UPLOADING.value)
        for issue in issues:
            if issue.task_id != '':
                res = file_task_connector.get_async_result(issue.task_id)
                if res.status == CeleryTaskStatus.SUCCESS.value:
                    data = res.get()
                    issue.status = FileUploadStatus.UPLOADED.value
                    issue.cid = data['cid']
                    issue.nft_url = data['nft_url']
                    issue.n_pages = data['n_pages']
                    issue.save()
                elif res.status == CeleryTaskStatus.FAILURE.value:
                    issue.status = FileUploadStatus.FAILURE.value
                    issue.save()
    except Exception as e:
        print(f'Exception when calling watch_celery_task: {e}')
