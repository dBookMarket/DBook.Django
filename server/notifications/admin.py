from django.contrib import admin
from . import models


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['receiver', 'title', 'message', 'is_read', 'created_at']
    search_fields = ['receiver__address', 'receiver__username', 'title', 'message']


admin.site.register(models.Notification, NotificationAdmin)
