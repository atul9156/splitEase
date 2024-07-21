from django.contrib import admin

from . import models

admin.site.register(models.User)
admin.site.register(models.Group)
admin.site.register(models.Membership)
admin.site.register(models.Transaction)
