from django.db import models
from utils.models import BaseModel
from stores.models import Trade
from utils.enums import IssueStatus, BlockChainType, CeleryTaskStatus
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import uuid
import os

encryption_storage = FileSystemStorage(location=settings.ENCRYPTION_ROOT)


class Draft(BaseModel):
    author = models.ForeignKey(to='users.User', to_field='id', related_name='draft_author', on_delete=models.CASCADE,
                               verbose_name='作者')
    title = models.CharField(max_length=150, verbose_name='标题')
    content = models.TextField(max_length=1000000, verbose_name='内容')

    class Meta:
        verbose_name = '草稿'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.title}-{self.author.name}'


class Book(BaseModel):
    author = models.ForeignKey(to='users.User', to_field='id', related_name='book_author', on_delete=models.RESTRICT,
                               verbose_name='作者')
    title = models.CharField(max_length=150, verbose_name='书籍名称')
    desc = models.TextField(max_length=1500, verbose_name='书籍描述')
    cover = models.ImageField(verbose_name='书籍封面', upload_to='covers')
    draft = models.ForeignKey(blank=True, to='Draft', to_field='id', related_name='book_draft',
                              on_delete=models.SET_NULL, null=True, verbose_name='草稿')
    file = models.FileField(upload_to='tmp', blank=True, null=True, default=None, verbose_name='文档')
    type = models.CharField(max_length=15, blank=True, default='pdf', verbose_name='文档类型')
    n_pages = models.IntegerField(blank=True, default=0, verbose_name='书籍总页数')
    # NFTStorage id
    cid = models.CharField(max_length=150, blank=True, default='', verbose_name='NFT asset id')

    status = models.CharField(max_length=50, choices=CeleryTaskStatus.choices(),
                              default=CeleryTaskStatus.PENDING.value, verbose_name='File upload status')
    # celery task status
    task_id = models.CharField(max_length=50, blank=True, default='', verbose_name='Celery task id')

    class Meta:
        # UnorderedObjectListWarning
        ordering = ['id']
        verbose_name = '书籍'
        verbose_name_plural = verbose_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.file:
            extension = os.path.splitext(self.file.name)[1].replace('.', '')
            self.type = extension.lower()
        super().save(force_insert, force_update, using, update_fields)


class Issue(BaseModel):
    id = models.UUIDField(verbose_name='id', primary_key=True, blank=True, default=uuid.uuid4())

    book = models.OneToOneField(to='Book', to_field='id', related_name='issue_book', verbose_name='书籍',
                                on_delete=models.CASCADE)

    quantity = models.IntegerField(blank=True, default=1, verbose_name='发行数量')
    price = models.FloatField(blank=True, default=0, verbose_name='发行价格')
    royalty = models.FloatField(blank=True, default=0, verbose_name='版税%')
    buy_limit = models.IntegerField(blank=True, default=1, verbose_name='购买限制')
    published_at = models.DateTimeField(verbose_name='发行时间')
    duration = models.IntegerField(verbose_name='发行时长(min)')
    n_circulations = models.IntegerField(blank=True, default=0, verbose_name='流通数量')
    # destroyed_quantity = models.IntegerField(blank=True, default=0, verbose_name='销毁数量')
    status = models.CharField(blank=True, max_length=50, choices=IssueStatus.choices(),
                              default=IssueStatus.PRE_SALE.value, verbose_name='发行状态')
    destroy_log = models.CharField(blank=True, default='', max_length=42, verbose_name='销毁地址')

    class Meta:
        ordering = ['id']
        verbose_name = '书籍出版'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.book.title


class Contract(BaseModel):
    book = models.OneToOneField(to='Book', to_field='id', related_name='contract_book',
                                on_delete=models.CASCADE, verbose_name='书籍')
    address = models.CharField(max_length=128, verbose_name='合约地址')

    criteria = models.CharField(max_length=150, blank=True, default='ERC1155', verbose_name='代币标准')
    block_chain = models.CharField(max_length=150, choices=BlockChainType.choices(),
                                   default=BlockChainType.POLYGON.value, verbose_name='区块链网络')
    token = models.CharField(max_length=150, blank=True, default='USDC', verbose_name='代币')

    class Meta:
        ordering = ['id', 'book']
        verbose_name = '书籍合约'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.book.title}'


class Bookmark(BaseModel):
    user = models.ForeignKey(to='users.User', to_field='id', related_name='bookmark_user',
                             on_delete=models.CASCADE, verbose_name='用户')
    book = models.ForeignKey(to='Book', to_field='id', related_name='bookmark_book', on_delete=models.CASCADE,
                             verbose_name='书籍')
    current_page = models.IntegerField(blank=True, default=0, verbose_name='当前阅读页码')

    class Meta:
        ordering = ['id', 'user', 'book']
        verbose_name = '书签'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.address}-{self.book.title}'


class Preview(BaseModel):
    book = models.OneToOneField(to='Book', to_field='id', related_name='preview_book',
                                on_delete=models.CASCADE, verbose_name='书籍')
    start_page = models.IntegerField(blank=True, default=1, verbose_name='起始页')
    n_pages = models.IntegerField(blank=True, default=10, verbose_name='预览页数')

    file = models.FileField(blank=True, default='', upload_to='previews')

    class Meta:
        ordering = ['id', 'book']
        verbose_name = '书籍预览'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.book.title}'

    def delete(self, using=None, keep_parents=False):
        if self.file:
            self.file.delete()
        super().delete(using, keep_parents)


class Asset(BaseModel):
    user = models.ForeignKey(to='users.User', to_field='id', related_name='asset_user',
                             on_delete=models.CASCADE, verbose_name='用户')
    book = models.ForeignKey(to='Book', to_field='id', related_name='asset_book',
                             on_delete=models.RESTRICT, verbose_name='书籍')
    quantity = models.IntegerField(blank=True, default=1)

    # decrypt the nft to a temporary file and send it to frontend
    # file = models.FileField(upload_to='tmp', blank=True, default='')

    class Meta:
        ordering = ['id']
        verbose_name = '个人资产'
        verbose_name_plural = verbose_name

    # def delete(self, using=None, keep_parents=False):
    #     if self.file:
    #         self.file.delete()
    #     super().delete(using, keep_parents)

    def __str__(self):
        return f'{self.user.address}-{self.book.title}'


class EncryptionKey(BaseModel):
    user = models.ForeignKey(to='users.User', to_field='id', related_name='encryption_key_user',
                             on_delete=models.CASCADE, verbose_name='用户')
    book = models.ForeignKey(to='Book', to_field='id', related_name='encryption_key_book', on_delete=models.CASCADE,
                             verbose_name='书籍')
    public_key = models.FileField(blank=True, upload_to=settings.PUBLIC_KEY_DIR, storage=encryption_storage,
                                  verbose_name='公钥文件')
    private_key = models.FileField(blank=True, upload_to=settings.PRIVATE_KEY_DIR, storage=encryption_storage,
                                   verbose_name='私钥文件')
    key_dict = models.FileField(blank=True, upload_to=settings.KEY_DICT_DIR, storage=encryption_storage,
                                verbose_name='密钥字典')
    key = models.CharField(blank=True, max_length=64, verbose_name='密钥')

    class Meta:
        verbose_name = '加密文件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.name

    def delete(self, using=None, keep_parents=False):
        if self.public_key:
            self.public_key.delete()
        if self.private_key:
            self.private_key.delete()
        if self.key_dict:
            self.key_dict.delete()
        super().delete(using, keep_parents)


class Wishlist(BaseModel):
    user = models.ForeignKey(to='users.User', to_field='id', related_name='wishlist_user', on_delete=models.CASCADE,
                             verbose_name='用户')
    issue = models.ForeignKey(to='Issue', to_field='id', related_name='wishlist_issue', on_delete=models.CASCADE,
                              verbose_name='发行书籍')

    class Meta:
        ordering = ['id']
        verbose_name = '心愿单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.name}-{self.issue.book.title}'


class Advertisement(BaseModel):
    issue = models.OneToOneField(to='Issue', to_field='id', related_name='advertisement_Issue',
                                 on_delete=models.CASCADE, verbose_name='书籍')
    show = models.BooleanField(blank=True, default=True, verbose_name='是否显示')

    class Meta:
        ordering = ['id']
        verbose_name = '广告'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.issue.book.title
