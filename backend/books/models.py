from django.db import models
from utils.models import BaseModel
from django.forms.models import model_to_dict
from stores.models import Trade
from utils.enums import IssueStatus
from django.conf import settings
from django.core.files.storage import FileSystemStorage

encryption_storage = FileSystemStorage(location=settings.ENCRYPTION_ROOT)


class Category(BaseModel):
    parent = models.ForeignKey(to='self', to_field='id', on_delete=models.SET_NULL, related_name='category_parent',
                               null=True, blank=True, default=None, verbose_name='所属类别')
    name = models.CharField(max_length=150, blank=False, verbose_name='类别名称')
    level = models.IntegerField(blank=True, default=1, verbose_name='类别层级')
    comment = models.CharField(max_length=200, blank=True, default='', verbose_name='备注')

    class Meta:
        ordering = ['id']
        verbose_name = '分类'
        verbose_name_plural = verbose_name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name


class Issue(BaseModel):
    category = models.ForeignKey(to='books.Category', to_field='id', related_name='book_category',
                                 on_delete=models.SET_NULL, null=True, blank=True, verbose_name='书籍分类')
    publisher = models.ForeignKey(to='accounts.User', to_field='account_addr', related_name='book_publisher',
                                  on_delete=models.CASCADE, verbose_name='发行商')

    # meta data
    author_name = models.CharField(max_length=150, verbose_name='作者名称')
    author_desc = models.TextField(max_length=1500,  blank=True, default='', verbose_name='作者描述')

    cover = models.ImageField(blank=True, default=None, verbose_name='书籍封面', upload_to='covers')
    name = models.CharField(max_length=150, verbose_name='书籍名称')
    desc = models.TextField(max_length=1500, verbose_name='书籍描述')
    n_pages = models.IntegerField(blank=True, default=0, verbose_name='书籍总页数')
    file = models.FileField(upload_to='tmp', blank=True, null=True, default=None, verbose_name='pdf文档')

    number = models.CharField(blank=True, max_length=50, verbose_name='Issue number')
    amount = models.IntegerField(blank=True, default=1, verbose_name='发行数量')
    price = models.FloatField(blank=True, default=0, verbose_name='发行价格')
    ratio = models.FloatField(blank=True, default=0.2, verbose_name='版税比例')

    # NFTStorage id
    cids = models.JSONField(blank=True, default=list, verbose_name='NFT asset ids')
    # cid = models.CharField(max_length=150, blank=True, default='', verbose_name='NFT asset id')
    # nft_url = models.URLField(blank=True, default='', verbose_name='NFT asset url')

    status = models.CharField(max_length=50, choices=IssueStatus.choices(),
                              default=IssueStatus.UPLOADING.value, verbose_name='File upload status')
    # celery task status
    task_id = models.CharField(max_length=50, blank=True, default='', verbose_name='Celery task id')

    class Meta:
        ordering = ['id', 'name', 'category']
        verbose_name = '发行书籍'
        verbose_name_plural = verbose_name

    @property
    def n_owners(self):
        """the number of whom owns this book"""
        return Asset.objects.filter(issue_id=self.id).count()

    @property
    def n_circulations(self):
        """the number of books in circulation"""
        queryset = Trade.objects.filter(issue_id=self.id)
        total_amount = 0
        if queryset:
            total_amount = queryset.aggregate(total_amount=models.Sum('amount'))['total_amount']
        return total_amount

    def __str__(self):
        return self.name


class Contract(BaseModel):
    issue = models.OneToOneField(to='books.Issue', to_field='id', related_name='contract_issue',
                                 on_delete=models.CASCADE, verbose_name='书籍')
    address = models.CharField(max_length=150, verbose_name='合约地址')

    token_amount = models.IntegerField(blank=True, default=0, verbose_name='代币数量')
    token_criteria = models.CharField(max_length=150, blank=True, default='ERC-1155', verbose_name='代币标准')
    block_chain = models.CharField(max_length=150, blank=True, default='Polygon', verbose_name='区块链')
    # 一本书发行后，其代币在后续挂单中无法修改？
    token = models.CharField(max_length=150, blank=True, default='USDT', verbose_name='代币')

    class Meta:
        ordering = ['id', 'issue']
        verbose_name = '书籍合约'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.issue.name}'


class Bookmark(BaseModel):
    user = models.ForeignKey(to='accounts.User', to_field='account_addr', related_name='bookmark_user',
                             on_delete=models.CASCADE, verbose_name='用户')
    issue = models.ForeignKey(to='books.Issue', to_field='id', related_name='bookmark_issue', on_delete=models.CASCADE,
                              verbose_name='书籍')
    current_page = models.IntegerField(blank=True, default=0, verbose_name='当前阅读页码')

    class Meta:
        ordering = ['id', 'user', 'issue']
        verbose_name = '书签'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.account_addr}-{self.issue.name}'


class Banner(BaseModel):
    img = models.ImageField(blank=True, default=None, verbose_name='宣传图', upload_to='images')
    name = models.CharField(max_length=150, verbose_name='宣传标语')
    desc = models.TextField(max_length=1500, verbose_name='宣传内容')
    redirect_url = models.URLField(blank=True, default=None)

    class Meta:
        ordering = ['id', 'name']
        verbose_name = 'banner'
        verbose_name_plural = verbose_name

    def delete(self, using=None, keep_parents=False):
        if self.img:
            self.img.delete()
        super().delete(using, keep_parents)

    def __str__(self):
        return self.name


class Preview(BaseModel):
    issue = models.OneToOneField(to='books.Issue', to_field='id', related_name='preview_issue',
                                 on_delete=models.CASCADE, verbose_name='书籍')
    start_page = models.IntegerField(blank=True, default=1, verbose_name='起始页')
    n_pages = models.IntegerField(blank=True, default=5, verbose_name='预览页数')

    file = models.FileField(blank=True, default='', upload_to='previews')

    class Meta:
        ordering = ['id', 'issue']
        verbose_name = '书籍预览'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.issue.name}'


class Asset(BaseModel):
    user = models.ForeignKey(to='accounts.User', to_field='account_addr', related_name='asset_user',
                             on_delete=models.CASCADE, verbose_name='用户')
    issue = models.ForeignKey(to='books.Issue', to_field='id', related_name='asset_issue',
                              on_delete=models.CASCADE, verbose_name='书籍')
    amount = models.IntegerField(blank=True, default=1)
    file = models.FileField(upload_to='tmp', blank=True, default='')

    class Meta:
        ordering = ['id', 'user', 'issue']
        verbose_name = '个人资产'
        verbose_name_plural = verbose_name

    @property
    def bookmark(self):
        instance, _ = Bookmark.objects.get_or_create(user=self.user, issue=self.issue, defaults={'current_page': 0})
        return model_to_dict(instance, fields=['id', 'issue', 'current_page'])

    def delete(self, using=None, keep_parents=False):
        if self.file:
            self.file.delete()
        super().delete(using, keep_parents)

    def __str__(self):
        return f'{self.user.account_addr}-{self.issue.name}'


class EncryptionKey(BaseModel):
    issue = models.OneToOneField(to='books.Issue', to_field='id', related_name='encryption_key_issue',
                                 on_delete=models.CASCADE, verbose_name='书籍')
    public_key = models.FileField(upload_to=settings.PUBLIC_KEY_DIR, storage=encryption_storage, verbose_name='公钥文件')
    private_key = models.FileField(upload_to=settings.PRIVATE_KEY_DIR, storage=encryption_storage, verbose_name='私钥文件')
    key_dict = models.FileField(upload_to=settings.KEY_DICT_DIR, storage=encryption_storage, verbose_name='密钥字典')

    class Meta:
        ordering = ['id', 'issue']
        verbose_name = '加密文件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.issue.name

    def delete(self, using=None, keep_parents=False):
        if self.public_key:
            self.public_key.delete()
        if self.private_key:
            self.private_key.delete()
        if self.key_dict:
            self.key_dict.delete()
        super().delete(using, keep_parents)
