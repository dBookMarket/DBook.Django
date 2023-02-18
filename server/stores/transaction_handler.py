from stores.models import Benefit
from books.models import Asset
from utils.enums import TransactionStatus
from utils.smart_contract_handler import ContractFactory
from utils.redis_accessor import RedisLock
from django.conf import settings
from django.db.transaction import atomic
from django.core.exceptions import ObjectDoesNotExist


class TransactionHandler:

    def __init__(self, obj):
        self.obj = obj

    @atomic
    def success(self):
        # 0, update issue
        if self.obj.trade.first_release:
            self.obj.issue.n_circulations += self.obj.quantity
            self.obj.issue.save()
        # 1, update trade
        self.obj.trade.quantity -= self.obj.quantity
        self.obj.trade.save()
        # 2, update seller asset
        if not self.obj.trade.first_release:
            obj_asset = Asset.objects.get(user=self.obj.trade.user, issue=self.obj.trade.issue)
            obj_asset.quantity -= self.obj.quantity
            obj_asset.save()
        # 3, update buyer asset
        try:
            obj_buyer_asset = Asset.objects.get(user=self.obj.buyer, issue=self.obj.trade.issue)
            obj_buyer_asset.quantity += self.obj.quantity
            obj_buyer_asset.save()
        except Asset.DoesNotExist:
            Asset.objects.create(user=self.obj.buyer, issue=self.obj.trade.issue, quantity=self.obj.quantity)
        # 4, update seller and author's benefit
        # first class market
        if self.obj.trade.first_release:
            author_rate = 1 - settings.PLATFORM_ROYALTY
            amount = self.obj.quantity * self.obj.price * author_rate
            Benefit.objects.update_or_create(user=self.obj.seller, transaction=self.obj, defaults={
                'amount': amount,
                'currency': self.obj.issue.token_issue.currency
            })
        else:
            # second class market
            author_rate = self.obj.issue.royalty / 100
            seller_rate = 1 - author_rate - settings.PLATFORM_ROYALTY
            t_amount = self.obj.quantity * self.obj.price
            author_amount = t_amount * author_rate
            seller_amount = t_amount * seller_rate
            Benefit.objects.update_or_create(user=self.obj.issue.book.author, transaction=self.obj, defaults={
                'amount': author_amount,
                'currency': self.obj.issue.token_issue.currency
            })
            Benefit.objects.update_or_create(user=self.obj.seller, transaction=self.obj, defaults={
                'amount': seller_amount,
                'currency': self.obj.issue.token_issue.currency
            })

    def pending(self):
        # call smart contract
        try:
            chain_type = self.obj.issue.token_issue.block_chain
        except ObjectDoesNotExist as e:
            print(f'Object does not exist -> {e}')
            return

        handler = ContractFactory(chain_type)
        payment = self.obj.quantity * self.obj.price * (1 - settings.PLATFORM_ROYALTY)

        try:
            # if it's a first trade, call the smart contract to send a transaction on block chain polygon or bnb.
            if bool(self.obj.trade.first_release and self.obj.issue.n_circulations == 0):
                with RedisLock(f'issue_first_transaction_lock_{self.obj.issue.id}'):
                    # if it's a first trade, call the smart contract to
                    # send a transaction on block chain polygon or bnb.
                    if bool(self.obj.trade.first_release and self.obj.issue.n_circulations == 0):
                        res = handler.first_trade(self.obj.seller.address, payment,
                                                  self.obj.buyer.address, self.obj.issue.token_issue.id,
                                                  self.obj.quantity, self.obj.issue.quantity)
                        if res['status'] == TransactionStatus.SUCCESS.value:
                            handler.set_token_info(self.obj.issue.token_issue.id, self.obj.seller.address,
                                                   self.obj.issue.royalty, self.obj.issue.price)
                        else:
                            # pay money back
                            pass
                    else:
                        res = handler.first_trade(self.obj.seller.address, payment, self.obj.buyer.address,
                                                  self.obj.issue.token_issue.id, self.obj.quantity)
            else:
                res = handler.first_trade(self.obj.seller.address, payment,
                                          self.obj.buyer.address, self.obj.issue.token_issue.id, self.obj.quantity)
        except Exception as e:
            print(f'Fail to set transaction for issue {self.obj.issue.id} -> {e}')
            self.obj.status = TransactionStatus.FAILURE.value
            self.obj.save()
        else:
            # update transaction info
            self.obj.hash = res['hash']
            self.obj.status = res['status']
            # avoid unlimited recursive
            if self.obj.status != TransactionStatus.PENDING.value:
                self.obj.save()

    def failure(self):
        pass

    def handle(self):
        func = getattr(self, self.obj.status, None)
        if func:
            func()
