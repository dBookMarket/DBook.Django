from stores.models import Trade
from utils.redis_handler import IssueQueue
import pytz
from datetime import timedelta


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
        # set timer for ending the sale
        end_time = self.obj.published_at + timedelta(minutes=self.obj.duration)
        utc_time = end_time.astimezone(pytz.UTC)
        IssueQueue().check_in(str(self.obj.id), utc_time.timestamp())

    def off_sale(self):
        # # destroy unsold books by calling smart contract
        # contract = ContractFactory(self.obj.token.block_chain)
        # txn_hash, is_destroyed = contract.burn(self.obj.book.author.address, self.obj.token.id,
        #                                        self.obj.quantity - self.obj.n_circulations)
        # print(f'Destroy NFT {self.obj.id} -> log: {txn_hash}')
        # self.obj.destroy_log = txn_hash
        # self.obj.save()
        # delete trade
        Trade.objects.filter(user=self.obj.book.author, issue=self.obj, first_release=True).delete()
        IssueQueue().check_out()

    def unsold(self):
        Trade.objects.filter(user=self.obj.book.author, issue=self.obj, first_release=True).delete()
        IssueQueue().check_out()

    def handle(self):
        _status = self.obj.status
        func = getattr(self, _status, None)
        if func is not None:
            func()
