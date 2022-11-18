from django.contrib import admin
from . import models


class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'desc', 'author', 'task_id', 'status']
    search_fields = ['title', 'desc', 'author__address', 'author__name', 'author__username', 'task_id', 'status']


class IssueAdmin(admin.ModelAdmin):
    list_display = ['id', 'book', 'quantity', 'price', 'status', 'n_circulations']
    search_fields = ['book__title', 'status']


admin.site.register(models.Draft)
admin.site.register(models.Book, BookAdmin)
admin.site.register(models.Issue, IssueAdmin)
admin.site.register(models.Bookmark)
admin.site.register(models.Asset)
admin.site.register(models.Contract)
admin.site.register(models.Preview)
admin.site.register(models.Wishlist)
admin.site.register(models.Advertisement)
