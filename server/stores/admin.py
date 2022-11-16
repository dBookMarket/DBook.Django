from django.contrib import admin
from . import models

admin.site.register(models.Trade)
admin.site.register(models.Transaction)
admin.site.register(models.Benefit)
