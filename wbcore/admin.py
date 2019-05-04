from django.contrib import admin
from .models import Address, Location, Host, Partner, Project, Event, NewsPost, BlogPost, Profile, ContactMessage
from .models import UserRelation, Document, Team, Milestone, Donation, Milestep, BankAccount, TeamUserRelation
from django.db import models
from modeltranslation.admin import TabbedTranslationAdmin
from tinymce import TinyMCE
from django_google_maps import widgets as map_widgets
from django_google_maps import fields as map_fields

class MyAdmin(admin.ModelAdmin):
    '''
    Implements a wysiwyg editor.
    '''
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(mce_attrs={'height': 200})},
        map_fields.AddressField: {'widget': map_widgets.GoogleMapsAddressWidget(attrs={'data-map-type': 'roadmap'})},

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
<<<<<<< HEAD
admin.site.register(TeamUserRelation, MyAdmin)
=======
admin.site.register(ContactMessage, MyAdmin)
>>>>>>> forms
