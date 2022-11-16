from django.contrib import admin
from . import models


class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'desc', 'author', 'task_id']
    search_fields = ['title', 'desc', 'author__address', 'author__name', 'author__username', 'task_id']


admin.site.register(models.Draft)
admin.site.register(models.Book, BookAdmin)
admin.site.register(models.Issue)
admin.site.register(models.Bookmark)
admin.site.register(models.Asset)
admin.site.register(models.Contract)
admin.site.register(models.Preview)
admin.site.register(models.Wishlist)
admin.site.register(models.Advertisement)
