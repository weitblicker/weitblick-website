from django.contrib import admin
from .models import Address, Location, Host, Partner, Project, Event, Post, Profile
from .models import CustomGallery, UserRelation, Document, Team, Milestone, Donation, Milestep, BankAccount
from django.db import models
from redactor.widgets import AdminRedactorEditor
from photologue.admin import GalleryAdmin as GalleryAdminDefault
from photologue.models import Gallery



class MyAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': AdminRedactorEditor},
    }
class GalleryExtendedInline(admin.StackedInline):
    model = CustomGallery
    can_delete = False

class GalleryAdmin(GalleryAdminDefault):
    """Define our new one-to-one model as an inline of Photologue's Gallery model."""
    inlines = [GalleryExtendedInline, ]

admin.site.unregister(Gallery)
admin.site.register(Gallery, GalleryAdmin)
admin.site.register(Address, MyAdmin)
admin.site.register(Location, MyAdmin)
admin.site.register(Host, MyAdmin)
admin.site.register(Partner, MyAdmin)
admin.site.register(Project, MyAdmin)
admin.site.register(Event, MyAdmin)
admin.site.register(Post, MyAdmin)
admin.site.register(Profile, MyAdmin)
admin.site.register(UserRelation, MyAdmin)
admin.site.register(Document, MyAdmin)
admin.site.register(Team, MyAdmin)
admin.site.register(Milestone, MyAdmin)
admin.site.register(Donation, MyAdmin)
admin.site.register(Milestep, MyAdmin)
admin.site.register(BankAccount, MyAdmin)

