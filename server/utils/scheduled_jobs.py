from books.models import Book, EncryptionKey, Issue
from stores.models import Transaction
from django.db.transaction import atomic
from utils.enums import CeleryTaskStatus, IssueStatus, TransactionStatus
from books.file_service_connector import FileServiceConnector
from utils.redis_handler import IssueQueue
from utils.smart_contract_handler import ContractFactory
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
                    # update book
                    book.status = current_status
                    book.cid = data['cid']
                    # book.n_pages = data['n_pages']
                    book.save()
                    # add key
                    EncryptionKey.objects.update_or_create(
                        defaults={'key': data['key']},
                        book=book,
                        user=book.author
                    )
                    # remove original file
                    if book.file:
                        book.file.delete()
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
                    # IssueHandler(issue).handle()
                    # # set timer for ending the sale
                    # end_time = issue.published_at + timedelta(minutes=issue.duration)
                    # utc_time = end_time.astimezone(pytz.UTC)
                    # que.check_in(str(issue.id), utc_time.timestamp())
                elif issue.status == IssueStatus.ON_SALE.value:
                    # update status
                    if issue.n_circulations > 0:
                        issue.status = IssueStatus.OFF_SALE.value
                        # destroy unsold books by calling smart contract
                        contract = ContractFactory(issue.token_issue.block_chain)
                        txn_hash, is_destroyed = contract.burn(issue.book.author.address, issue.token_issue.id,
                                                               issue.quantity - issue.n_circulations)
                        print(f'Destroy NFT {issue.id} -> log: {txn_hash}')
                        issue.destroy_log = txn_hash
                    else:
                        issue.status = IssueStatus.UNSOLD.value
                    issue.save()
                    # make it clean after sale
                    # IssueHandler(issue).handle()
                    # quit queue
                    # que.check_out()
                # else:
                #     IssueHandler(issue).handle()
                    # que.check_out()
                IssueHandler(issue).handle()


def pay_back():
    """
    If some transaction is first release and failed, return money back to the buyer and remove this transaction
    Only deal with the oldest five transactions per time because of the high cost of smart contract's operation
    """
    print('Money back to the buyers...')
    queryset = Transaction.objects.filter(status=TransactionStatus.FAILURE.value, trade__first_release=True).order_by(
        'created_at')
    for txn in queryset[:5]:
        try:
            contract_handler = ContractFactory(txn.issue.token_issue.block_chain)
            success = contract_handler.pay_back(txn.buyer.address, txn.quantity * txn.price)
            if success:
                txn.delete()
        except Exception as e:
            print(f'Exception when paying back to the buyer -> {e}')
            pass
