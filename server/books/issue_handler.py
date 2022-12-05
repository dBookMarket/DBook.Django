from stores.models import Trade
from utils.redis_handler import IssueQueue
from utils.smart_contract_handler import ContractFactory
from django.db.transaction import atomic
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
        # destroy unsold books by calling smart contract
        contract = ContractFactory(self.obj.token_issue.block_chain)
        txn_hash, isDestroyed = contract.burn(self.obj.book.author.address, self.obj.token_issue.id,
                                              self.obj.quantity-self.obj.n_circulations)
        print(f'Destroy NFT -> log: {txn_hash}')
        self.obj.destroy_log = txn_hash
        self.obj.save()
        # delete trade
        Trade.objects.get(user=self.obj.book.author, issue=self.obj, first_release=True).delete()

    def unsold(self):
        Trade.objects.filter(user=self.obj.book.author, issue=self.obj, first_release=True).delete()

    def handle(self):
        _status = self.obj.status
        func = getattr(self, _status, None)
        if func is not None:
            with atomic():
                func()
