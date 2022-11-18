from stores.models import Trade
from books.models import Issue
from utils.enums import IssueStatus
from utils.redis_handler import IssueQueue
from datetime import timedelta
from django.db.transaction import atomic


class IssueHandler:

    def __init__(self, obj):
        self.obj = obj

    def pre_sale(self):
        # send the issue to a queue
        que = IssueQueue()
        que.check_in(self.obj.id, self.obj.published_at.timestamp())

    def on_sale(self):
        Trade.objects.update_or_create(user=self.obj.book.author, book=self.obj.book, defaults={
            'first_release': True,
            'quantity': self.obj.quantity,
            'price': self.obj.price
        })

    def off_sale(self):
        # todo destroy unsold books by calling smart contract
        Trade.objects.get(user=self.obj.book.author, book=self.obj.book, first_release=True).delete()

    def unsold(self):
        # todo destroy unsold books by calling smart contract
        Trade.objects.filter(user=self.obj.book.author, book=self.obj.book, first_release=True).delete()

    def handle(self):
        _status = self.obj.status
        func = getattr(self, _status, None)
        if func:
            func()


def issue_timer():
    que = IssueQueue()
    issues = que.get_top()
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
                    que.check_in(issue.id, end_time.timestamp())
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
                    que.check_out(issue.id)
