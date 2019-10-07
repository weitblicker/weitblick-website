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
from copy import copy

from itertools import chain

from .models import (
    Address, Location, Host, Partner, Project, Event, NewsPost, BlogPost, ContactMessage, UserRelation,
    Document, Team, Milestone, Donation, Milestep, BankAccount, TeamUserRelation, Content, User, JoinPage
)


class MyTranslatedAdmin(TabbedTranslationAdmin):
    '''
    Creates Tabs to handle languages.
    '''

    pass


class UserRelationInlineModel(admin.StackedInline):
    model = User.hosts.through

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        return formset

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return fields

    def get_queryset(self, request):
        admin_hosts = request.user.get_maintaining_hosts()
        queryset = super().get_queryset(request)
        if request.user.is_super_admin:
            return queryset

        queryset = queryset.exclude(user__is_super_admin=True)

        request_user_relations = queryset.filter(user=request.user)

        admin_hosts = request.user.get_maintaining_hosts()
        if admin_hosts:
            queryset = queryset.filter(host__in=admin_hosts)

        return queryset | request_user_relations

    def formfield_for_choice_field(self, db_field, request=None, **kwargs):
        formfield = super().formfield_for_choice_field(db_field, request, **kwargs)

        if request and request.user.is_super_admin:
            return formfield
        if db_field.name == 'member_type':

            print(kwargs)
            choices = dict(db_field.get_choices())
            del choices['admin']
            del choices['']
            kwargs['choices'] = tuple(choices.items())

        return db_field.formfield(**kwargs)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if request.user.is_super_admin:
            return readonly_fields

        if not UserAdmin.is_admin_of(request, obj) or obj == request.user:
            readonly_fields += ('member_type',)

        readonly_fields += ('host', 'membership_fee')

        return readonly_fields

    def has_add_permission(self, request):
        if request.user.is_super_admin:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_super_admin:
            return True

        # allow host admins to change some details, see readonly fields
        if UserAdmin.is_admin_of(request, obj):
            return True

        # all others are not allows to change their profile
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user == obj:
            return False
        return UserAdmin.is_admin_of(request, obj)

    def has_view_permission(self, request, obj=None):
        # user is allowed to see his / her own profile
        if obj is None:
            return True

        if request.user == obj:
            print("user has view permission!")
            return True

        # host admins can see all users and relations ships of the host they are admins in.
        return UserAdmin.is_admin_of(request, obj)

    def has_view_or_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj) or self.has_change_permission(request, obj)

    def has_module_permission(self, request):
        if request.user.is_authenticated:
            return True
        else:
            return False


class TeamUserRelationInlineModel(admin.TabularInline):
    model = Team.member.through


class JoinPageInlineModel(admin.StackedInline):
    model = JoinPage

    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(mce_attrs={'height': 200})},
        map_fields.AddressField: {'widget': map_widgets.GoogleMapsAddressWidget(attrs={'data-map-type': 'roadmap'})},
    }


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
        opts = self.opts
        codename = get_permission_codename('add', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_change_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('change', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)

    def has_delete_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('delete', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)

    def has_view_permission(self, request, obj=None):
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
        return request.user.has_module_perms(self.opts.app_label)


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
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
        model = User
        fields = ('is_super_admin', 'email', 'password', 'date_of_birth', 'is_active', 'first_name', 'last_name')
        exclude = ()

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    class RoleListFilter(admin.SimpleListFilter):
        title = 'Role'
        parameter_name = 'role'

        def lookups(self, request, model_admin):
            return UserRelation.TYPE_CHOICES

        def queryset(self, request, queryset):
            if self.value():
                queryset = queryset.filter(userrelation__member_type=self.value())
            return queryset

    class HostListFilter(admin.SimpleListFilter):
        title = 'Host'
        parameter_name = 'host'

        def lookups(self, request, model_admin):
            if request.user.is_super_admin:
                return [(host.slug, host.name) for host in Host.objects.all()]

            return [(host.slug, host.name) for host in request.user.hosts.all()]

        def queryset(self, request, queryset):
            if self.value():
                queryset = queryset.filter(userrelation__host__slug=self.value())
            return queryset

    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('name', 'email', 'date_of_birth', 'role')
    list_filter = (HostListFilter, RoleListFilter,)
    fieldsets = (
        ('Account', {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'date_of_birth',)}),
    )

    exclude = ()
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

    def get_fieldsets(self, request, obj=None):
        fieldset = super().get_fieldsets(request, obj)
        if request.user.is_super_admin:
            fieldset_dict = dict(fieldset)
            if 'is_super_admin' not in fieldset_dict['Account']['fields']:
                fieldset_dict['Account']['fields'] += ('is_super_admin',)
        else:
            fieldset_dict = dict(fieldset)
            fieldset_sublist = list(fieldset_dict['Account']['fields'])
            if 'is_super_admin' in fieldset_sublist:
                fieldset_sublist.remove('is_super_admin')
                fieldset_dict['Account']['fields'] = tuple(fieldset_sublist)

        return fieldset

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)

        if request.user.is_super_admin and request.user == obj:
            readonly_fields += ('is_super_admin',)

        if request.user.is_super_admin:
            return readonly_fields

        readonly_fields += ('email',)
        return readonly_fields

    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj)
        if not request.user.is_super_admin:
            exclude = exclude + ('is_super_admin',)
        return exclude

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return fields

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        # super user can see everything
        if request.user.is_super_admin:
            return queryset.distinct()

        admin_in_hosts = request.user.get_maintaining_hosts()
        if admin_in_hosts:
            return queryset.filter(hosts__in=request.user.get_maintaining_hosts())

        return queryset.filter(pk=request.user.pk)

    @staticmethod
    def is_admin_of(request, other_user):
        if request.user.is_super_admin:
            return True
        user_admin_hosts = request.user.get_maintaining_hosts()
        if user_admin_hosts:
            if other_user:
                if other_user.userrelation_set.filter(host__in=user_admin_hosts):
                    return True
                return False
            return True
        return False

    def has_add_permission(self, request):
        if request.user.is_super_admin:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return any((UserAdmin.is_admin_of(request, obj), request.user == obj))

    def has_delete_permission(self, request, obj=None):
        if request.user.is_super_admin:
            return True
        if request.user == obj:
            return False
        return UserAdmin.is_admin_of(request, obj)

    def has_view_permission(self, request, obj=None):
        return any((obj is None, UserAdmin.is_admin_of(request, obj), request.user == obj))

    def has_view_or_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj) or self.has_change_permission(request, obj)

    def has_module_permission(self, request):
        if request.user.is_authenticated:
            return True
        else:
            return False


class TeamAdmin(MyAdmin):
    inlines = (TeamUserRelationInlineModel,)


class HostAdmin(MyAdmin):
    inlines = (JoinPageInlineModel,)

# since we're not using Django's built-in permissions,
# register our own user model and unregister the Group model from admin.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)

admin.site.register(Address, MyAdmin)
admin.site.register(Content, MyAdmin)
admin.site.register(Location, MyAdmin)
admin.site.register(Host, HostAdmin)
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
