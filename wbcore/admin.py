from django.contrib import admin
from .models import Address, Location, Host, Partner, Project, Event, NewsPost, BlogPost, Profile
from .models import UserRelation, Document, Team, Milestone, Donation, Milestep, BankAccount
from django.db import models
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
    

admin.site.register(Address, MyTranslatedAdmin)
admin.site.register(Location, MyTranslatedAdmin)
admin.site.register(Host, MyTranslatedAdmin)
admin.site.register(Partner, MyTranslatedAdmin)
admin.site.register(Project, MyTranslatedAdmin)
admin.site.register(Event, MyTranslatedAdmin)
admin.site.register(NewsPost, MyTranslatedAdmin)
admin.site.register(Profile, MyAdmin)
admin.site.register(UserRelation, MyAdmin)
admin.site.register(Document, MyTranslatedAdmin)
admin.site.register(Team, MyTranslatedAdmin)
admin.site.register(Milestone, MyAdmin)
admin.site.register(Donation, MyAdmin)
admin.site.register(Milestep, MyTranslatedAdmin)
admin.site.register(BankAccount, MyAdmin)
admin.site.register(BlogPost, MyTranslatedAdmin)


