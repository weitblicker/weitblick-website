from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth import get_permission_codename
from django import forms

from django.db import models
from modeltranslation.admin import TabbedTranslationAdmin
from tinymce import TinyMCE
from django_google_maps import widgets as map_widgets
from django_google_maps import fields as map_fields

from .models import (
    Address, Location, Host, Partner, Project, Event, NewsPost, BlogPost, ContactMessage, UserRelation,
    Document, Team, Milestone, Donation, Milestep, BankAccount, TeamUserRelation, Content, MyUser
)


class MyTranslatedAdmin(TabbedTranslationAdmin):
    '''
    Creates Tabs to handle languages.
    '''

    pass


class UserRelationInlineModel(admin.StackedInline):
    model = MyUser.hosts.through



class TeamUserRelationInlineModel(admin.TabularInline):
    model = Team.member.through



class MyAdmin(admin.ModelAdmin):
    '''
    Implements a wysiwyg editor.
    '''
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(mce_attrs={'height': 200})},
        map_fields.AddressField: {'widget': map_widgets.GoogleMapsAddressWidget(attrs={'data-map-type': 'roadmap'})},
    }

    def get_queryset(self, request):
        queryset = super(MyAdmin, self).get_queryset(request)

        # super user can see everything
        if request.user.is_super_admin:
            return queryset

        # if model is host display the users hosts
        if queryset.model is Host:
            return request.user.hosts.all()

        # if many to many field hosts exists filter using it
        try:
            return queryset.filter(hosts__in=request.user.hosts.all())
        except:
            # if field host exists filter using it
            try:
                return queryset.filter(host__in=request.user.hosts.all())
            except:
                return queryset

    def has_add_permission(self, request):
        """
        Return True if the given request has permission to add an object.
        Can be overridden by the user in subclasses.
        """
        opts = self.opts
        codename = get_permission_codename('add', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_change_permission(self, request, obj=None):
        """
        Return True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to change the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to change *any* object of the given type.
        """
        opts = self.opts
        codename = get_permission_codename('change', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)

    def has_delete_permission(self, request, obj=None):
        """
        Return True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to delete the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to delete *any* object of the given type.
        """
        opts = self.opts
        codename = get_permission_codename('delete', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)

    def has_view_permission(self, request, obj=None):
        """
        Return True if the given request has permission to view the given
        Django model instance. The default implementation doesn't examine the
        `obj` parameter.

        If overridden by the user in subclasses, it should return True if the
        given request has permission to view the `obj` model instance. If `obj`
        is None, it should return True if the request has permission to view
        any object of the given type.
        """

        opts = self.opts
        codename_view = get_permission_codename('view', opts)
        codename_change = get_permission_codename('change', opts)
        return (
                request.user.has_perm('%s.%s' % (opts.app_label, codename_view), obj) or
                request.user.has_perm('%s.%s' % (opts.app_label, codename_change), obj)
        )

    def has_view_or_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj) or self.has_change_permission(request, obj)

    def has_module_permission(self, request):
        """
        Return True if the given request has any permission in the given
        app label.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to view the module on
        the admin index page and access the module's index page. Overriding it
        does not restrict access to the add, change or delete views. Use
        `ModelAdmin.has_(add|change|delete)_permission` for that.
        """
        return request.user.has_module_perms(self.opts.app_label)


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ('first_name', 'last_name', 'email', 'date_of_birth')
        exclude = ()

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
        fields = ('email', 'password', 'date_of_birth', 'is_active', 'first_name', 'last_name')
        exclude = ()

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
    list_display = ('name', 'email', 'date_of_birth')
    list_filter = ('hosts', 'role')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'date_of_birth',)}),
        ('Permissions', {'fields': ('role',)}),
    )
    inlines = (UserRelationInlineModel,)

    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'date_of_birth', 'password1', 'password2'),
        },),
    )
    search_fields = ('email',)
    ordering = ('email', 'hosts')
    filter_horizontal = ()

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        formfield = super(UserAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)
        print(**kwargs)
        print(formfield)
        if db_field is not 'role':
            return formfield
        #elif request.user.is_super_admin:
        #    return formfield
        else:
            if request.user.role is 'host_admin':
                return formfield
        #return formfield

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(UserAdmin, self). get_readonly_fields(request, obj)

        if request.user is obj:
            return readonly_fields + ('role',)
        elif request.user.is_super_admin:
            return readonly_fields
        elif not request.user.role is 'host_admin':
            return readonly_fields + ('role',)

        return  readonly_fields

    def get_fields(self, request, obj=None):
        fields = super(UserAdmin, self).get_fields(request, obj)
        return fields


class TeamAdmin(MyAdmin):
    inlines = (TeamUserRelationInlineModel,)


# since we're not using Django's built-in permissions,
# register our own user model and unregister the Group model from admin.
admin.site.unregister(MyUser)
admin.site.register(MyUser, UserAdmin)
admin.site.unregister(Group)


admin.site.register(Address, MyAdmin)
admin.site.register(Content, MyAdmin)
admin.site.register(Location, MyAdmin)
admin.site.register(Host, MyAdmin)
admin.site.register(Partner, MyAdmin)
admin.site.register(Project, MyAdmin)
admin.site.register(Event, MyAdmin)
admin.site.register(NewsPost, MyAdmin)
admin.site.register(Document, MyAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Milestone, MyAdmin)
admin.site.register(Donation, MyAdmin)
admin.site.register(Milestep, MyAdmin)
admin.site.register(BlogPost, MyAdmin)
admin.site.register(BankAccount, MyAdmin)
admin.site.register(ContactMessage, MyAdmin)
