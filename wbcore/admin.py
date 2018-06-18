from django.contrib import admin
from .models import Address, Location, Host, Partner, Project, Event, Post, Profile
from django.db import models
from redactor.widgets import AdminRedactorEditor


class MyAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': AdminRedactorEditor},
    }


admin.site.register(Address, MyAdmin)
admin.site.register(Location, MyAdmin)
admin.site.register(Host, MyAdmin)
admin.site.register(Partner, MyAdmin)
admin.site.register(Project, MyAdmin)
admin.site.register(Event, MyAdmin)
admin.site.register(Post, MyAdmin)
admin.site.register(Profile, MyAdmin)

# Register your models here.
