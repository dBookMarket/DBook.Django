from stores.models import Trade


class IssueHandler:

    def __init__(self, obj):
        self.obj = obj

    def pre_sale(self):
        # todo set a timer to listen the issue tasks
        #  send the issue to a queue
        pass

    def on_sale(self):
        Trade.objects.update_or_create(user=self.obj.book.author, book=self.obj.book, defaults={
            'first_release': True,
            'quantity': self.obj.quantity,
            'price': self.obj.price
        })
        # todo set a timer to listen to issue tasks
        #  send the issue to a queue

    def off_sale(self):
        # todo destroy unsold books by calling smart contract
        obj_trade = Trade.objects.get(user=self.obj.book.author, book=self.obj.book, first_release=True)
        # update number of circulations
        # update issue
        self.obj.n_circulations = self.obj.quantity - obj_trade.quantity
        self.obj.save()
        # remove first release
        obj_trade.delete()

    def unsold(self):
        # todo destroy unsold books by calling smart contract
        Trade.objects.filter(user=self.obj.book.author, book=self.obj.book, first_release=True).delete()

    def handle(self):
        _status = self.obj.status
        func = getattr(self, _status, None)
        if func:
            func()
