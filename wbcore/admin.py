from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django import forms

from django.db import models
from modeltranslation.admin import TabbedTranslationAdmin
from tinymce import TinyMCE
from django_google_maps import widgets as map_widgets
from django_google_maps import fields as map_fields

from .models import (
    Address, Location, Host, Partner, Project, Event, NewsPost, BlogPost, Profile, ContactMessage, UserRelation,
    Document, Team, Milestone, Donation, Milestep, BankAccount, TeamUserRelation, Content, MyUser
)


class MyAdmin(admin.ModelAdmin):
    '''
    Implements a wysiwyg editor.
    '''
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(mce_attrs={'height': 200})},
        map_fields.AddressField: {'widget': map_widgets.GoogleMapsAddressWidget(attrs={'data-map-type': 'roadmap'})},

    }


class MyTranslatedAdmin(MyAdmin, TabbedTranslationAdmin):
    '''
    Creates Tabs to handle languages.
    '''

    pass


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ('email', 'date_of_birth')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = MyUser
        fields = ('email', 'password', 'date_of_birth', 'is_active', 'is_admin')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'date_of_birth', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('date_of_birth',)}),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'date_of_birth', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


# Now register the new UserAdmin...
admin.site.register(MyUser, UserAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)


admin.site.register(Address, MyTranslatedAdmin)
admin.site.register(Content, MyTranslatedAdmin)
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
admin.site.register(BlogPost, MyTranslatedAdmin)
admin.site.register(BankAccount, MyAdmin)
admin.site.register(TeamUserRelation, MyAdmin)
admin.site.register(ContactMessage, MyAdmin)
