from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Wallet)
admin.site.register(models.Payment)
admin.site.register(models.Transaction)
admin.site.register(models.Refund)
