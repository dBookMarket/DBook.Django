from stores.models import Trade
from utils.redis_handler import IssueQueue
import pytz


class IssueHandler:

    def __init__(self, obj):
        self.obj = obj

    def pre_sale(self):
        # send the issue to a queue
        print(f'pre sale, published at {self.obj.published_at}')
        utc_time = self.obj.published_at.astimezone(pytz.UTC)
        print(f'utc time {utc_time}')
        que = IssueQueue()
        que.check_in(str(self.obj.id), utc_time.timestamp())

    def on_sale(self):
        Trade.objects.update_or_create(user=self.obj.book.author, issue=self.obj, defaults={
            'first_release': True,
            'quantity': self.obj.quantity,
            'price': self.obj.price
        })

    def off_sale(self):
        # todo destroy unsold books by calling smart contract
        Trade.objects.get(user=self.obj.book.author, issue=self.obj, first_release=True).delete()

    def unsold(self):
        # todo destroy unsold books by calling smart contract
        Trade.objects.filter(user=self.obj.book.author, issue=self.obj, first_release=True).delete()

    def handle(self):
        _status = self.obj.status
        func = getattr(self, _status, None)
        if func is not None:
            func()
