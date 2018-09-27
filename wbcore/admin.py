from django.contrib import admin
from .models import Address, Location, Host, Partner, Project, Event, Post, Profile
from .models import CustomGallery, UserRelation, Document, Team, Milestone, Donation, Milestep, BankAccount
from django.db import models
from photologue.admin import GalleryAdmin as GalleryAdminDefault
from photologue.models import Gallery
from modeltranslation.admin import TabbedTranslationAdmin
from tinymce import TinyMCE



class MyAdmin(admin.ModelAdmin):
    '''
    Implements a wysiwyg editor. 
    '''
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(mce_attrs={'height': 200})},
    }

class MyTranslatedAdmin(MyAdmin,TabbedTranslationAdmin):
    '''
    Creates Tabs to handle languages.
    '''
    
    pass
    

class GalleryExtendedInline(admin.StackedInline):
    model = CustomGallery
    can_delete = False

class GalleryAdmin(GalleryAdminDefault):
    """Define our new one-to-one model as an inline of Photologue's Gallery model."""
    inlines = [GalleryExtendedInline, ]

admin.site.unregister(Gallery)
admin.site.register(Gallery, GalleryAdmin)
admin.site.register(Address, MyTranslatedAdmin)
admin.site.register(Location, MyTranslatedAdmin)
admin.site.register(Host, MyTranslatedAdmin)
admin.site.register(Partner, MyTranslatedAdmin)
admin.site.register(Project, MyTranslatedAdmin)
admin.site.register(Event, MyTranslatedAdmin)
admin.site.register(Post, MyTranslatedAdmin)
admin.site.register(Profile, MyAdmin)
admin.site.register(UserRelation, MyAdmin)
admin.site.register(Document, MyTranslatedAdmin)
admin.site.register(Team, MyTranslatedAdmin)
admin.site.register(Milestone, MyAdmin)
admin.site.register(Donation, MyAdmin)
admin.site.register(Milestep, MyTranslatedAdmin)
admin.site.register(BankAccount, MyAdmin)


