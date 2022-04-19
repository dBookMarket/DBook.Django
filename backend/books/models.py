from django.db import models
from utils.models import BaseModel
from django.forms.models import model_to_dict


class Category(BaseModel):
    parent = models.ForeignKey(to='self', to_field='id', on_delete=models.SET_NULL, related_name='category_parent',
                               null=True, blank=True, default=None, verbose_name='所属类别')
    name = models.CharField(max_length=150, blank=False, verbose_name='类别名称')
    level = models.IntegerField(blank=True, default=1, verbose_name='类别层级')
    comment = models.CharField(max_length=200, blank=True, default='', verbose_name='备注')

    class Meta:
        ordering = ['level']
        verbose_name = '分类'
        verbose_name_plural = verbose_name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.parent:
            self.level = self.parent.level + 1
        super().save(force_insert, force_update, using, update_fields)


class Issue(BaseModel):
    category = models.ForeignKey(to='books.Category', to_field='id', related_name='book_category',
                                 on_delete=models.SET_NULL, null=True, blank=True, verbose_name='书籍分类')
    publisher = models.ForeignKey(to='accounts.User', to_field='account_addr', related_name='book_publisher',
                                  on_delete=models.CASCADE, verbose_name='发行商')

    # meta data
    author_name = models.CharField(max_length=150, verbose_name='作者名称')
    author_desc = models.TextField(max_length=1500, verbose_name='作者描述')

    cover = models.ImageField(blank=True, default=None, verbose_name='书籍封面', upload_to='covers')
    name = models.CharField(max_length=150, verbose_name='书籍名称')
    desc = models.TextField(max_length=1500, verbose_name='书籍描述')
    n_pages = models.IntegerField(blank=True, default=0, verbose_name='书籍总页数')

    number = models.CharField(blank=True, max_length=50, verbose_name='Issue number')
    amount = models.IntegerField(blank=True, default=1, verbose_name='发行数量')
    price = models.FloatField(blank=True, default=0, verbose_name='发行价格')
    ratio = models.FloatField(blank=True, default=0.2, verbose_name='版税比例')

    # NFTStorage id
    cid = models.CharField(max_length=150, unique=True, db_index=True, verbose_name='NFT asset id')
    nft_url = models.URLField(blank=True, verbose_name='NFT asset url')

    class Meta:
        ordering = ['id', 'name', 'category']
        verbose_name = '发行书籍'
        verbose_name_plural = verbose_name

    @property
    def contract(self):
        return Contract.objects.get(issue=self.id)

    @property
    def preview(self):
        return Preview.objects.get(issue=self.id)


class Contract(BaseModel):
    issue = models.OneToOneField(to='books.Issue', to_field='id', related_name='contract_issue',
                                 on_delete=models.CASCADE, verbose_name='书籍')
    address = models.CharField(max_length=150, unique=True, db_index=True, verbose_name='合约地址')

    token_amount = models.IntegerField(blank=True, default=0, verbose_name='代币数量')
    token_criteria = models.CharField(max_length=150, blank=True, default='ERC-1155', verbose_name='代币标准')
    block_chain = models.CharField(max_length=150, blank=True, default='Polygon', verbose_name='区块链')
    # 一本书发行后，其代币在后续挂单中无法修改？
    token = models.CharField(max_length=150, blank=True, default='USDT', verbose_name='代币')

    class Meta:
        ordering = ['id', 'issue']
        verbose_name = '书籍合约'
        verbose_name_plural = verbose_name


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
