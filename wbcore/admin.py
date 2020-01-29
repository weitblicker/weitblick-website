from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.admin import GenericInlineModelAdmin, GenericStackedInline, GenericTabularInline
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth import get_permission_codename
from django import forms
from django.db import models
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from martor.widgets import AdminMartorWidget
from django_google_maps import widgets as map_widgets
from django_google_maps import fields as map_fields
from schedule.models import Calendar
from copy import copy
from django_reverse_admin import ReverseModelAdmin
from rules.contrib.admin import ObjectPermissionsModelAdmin

from itertools import chain

from .models import (
    Address, Location, Host, Partner, Project, Event, NewsPost, BlogPost, ContactMessage, UserRelation,
    Document, Team, Milestone, Donation, BankAccount, TeamUserRelation, Content, User, JoinPage,
    SocialMediaLink, CycleDonation, QuestionAndAnswer, FAQ, Photo)


class MyTranslatedAdmin(TabbedTranslationAdmin):
    '''
    Creates Tabs to handle languages.
    '''

    pass


class PermissionInlineModel(TranslationTabularInline):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_super_admin:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'host':
            hosts = request.user.get_hosts_for_admin()
            kwargs["queryset"] = Host.objects.filter(pk__in=[host.pk for host in hosts])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('add', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)

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


class UserRelationInlineModel(PermissionInlineModel):
    model = User.hosts.through
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        return formset

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return fields

    def get_queryset(self, request):
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

            choices = dict(db_field.get_choices())
            del choices['admin']
            del choices['']
            kwargs['choices'] = tuple(choices.items())

        return db_field.formfield(**kwargs)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if request.user.is_super_admin or not obj:
            return readonly_fields

        if not UserAdmin.is_admin_of(request, obj) or obj == request.user:
            readonly_fields += ('member_type',)

        readonly_fields += ('host', 'membership_fee')

        return readonly_fields


class TeamUserRelationInlineModel(PermissionInlineModel):
    model = Team.member.through
    extra = 1


class MilestoneInlineModel(PermissionInlineModel):
    model = Milestone


class JoinPageInlineModel(PermissionInlineModel):
    model = JoinPage

    formfield_overrides = {
        models.TextField: {'widget': AdminMartorWidget},
        map_fields.AddressField: {'widget': map_widgets.GoogleMapsAddressWidget(attrs={'data-map-type': 'roadmap'})},
    }


class SocialMediaLinkInlineModel(PermissionInlineModel):
    model = SocialMediaLink
    extra = 1
    show_change_link = True


class AddressInlineModel(PermissionInlineModel):
    model = Address
    can_delete = False


class QuestionAndAnswerInlineModel(PermissionInlineModel):
    model = QuestionAndAnswer
    show_change_link = True


class MyAdmin(TabbedTranslationAdmin):
    class Media:
        js=('semantic/dist/semantic.min.js', 'js/wbcore.js')
        
    formfield_overrides = {
        models.TextField: {'widget': AdminMartorWidget},
        map_fields.AddressField: {'widget': map_widgets.GoogleMapsAddressWidget(attrs={'data-map-type': 'roadmap'})},
    }

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if request.user.is_super_admin:
            return super().formfield_for_manytomany(db_field, request, **kwargs)

        if db_field.name == 'hosts':
            if request.user.hosts.count() == 1:
                # setting the user from the request object
                kwargs['initial'] = request.user.hosts.all()
                # making the field readonly
                kwargs['disabled'] = True
            kwargs["queryset"] = request.user.hosts

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj)
        exclude = exclude if exclude else ()
        if request.user.is_super_admin:
            return exclude
        if request.user.hosts.count() == 1:
            exclude += ('hosts', 'host')

        return exclude

    def save_model(self, request, obj, form, change):
        if request.user.is_super_admin:
            super().save_model(request, obj, form, change)
            return

        if request.user.hosts.count() == 1:
            super().save_model(request, obj, form, change)
            if hasattr(obj, 'host'):
                obj.host = request.user.hosts.all()[0]
            elif hasattr(obj, 'hosts'):
                obj.hosts.set(request.user.hosts.all())

        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_super_admin:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'author':
            # setting the user from the request object
            kwargs['initial'] = request.user.pk
            # making the field readonly
            kwargs['disabled'] = True

        if db_field.name == 'host':
            if request.user.hosts.count() == 1:
                # setting the hosts the user belongs to from the request object
                kwargs['initial'] = request.user.hosts.all()[0].pk
                # making the field readonly
                kwargs['disabled'] = True
            else:
                hosts = request.user.get_hosts_for_admin()
                kwargs["queryset"] = Host.objects.filter(pk__in=[host.pk for host in hosts])

        if db_field.name == 'project':
                hosts = request.user.hosts.all()
                kwargs["queryset"] = Project.objects.filter(hosts__in=hosts).all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
        ret = request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)
        return ret

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
        fields = ('first_name', 'last_name', 'username', 'email', 'date_of_birth')
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
        fields = ('is_super_admin', 'email', 'username', 'password',
                  'date_of_birth', 'is_active', 'first_name', 'last_name', 'image')
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
            choices = ()
            if request.user.is_superuser:
                choices += (('is_super_admin', 'Super Admin'),)
            choices += (('no_relation', 'No Relation'),)
            choices += UserRelation.TYPE_CHOICES
            return choices

        def queryset(self, request, queryset):
            if self.value():
                if self.value() == 'is_super_admin':
                    queryset = queryset.filter(is_super_admin=True).exclude(is_super_admin=False)
                elif self.value() == 'no_relation':
                    queryset = queryset.filter(userrelation=None)
                else:
                    queryset = queryset.filter(userrelation__member_type=self.value())
            return queryset.distinct()

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
            return queryset.distinct()

    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('username', 'name', 'email', 'date_of_birth', 'get_hosts', 'get_roles',)
    list_filter = (HostListFilter, RoleListFilter,)
    fieldsets = (
        ('Account', {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'date_of_birth',)}),
        ('Profile', {'fields': ('image', )}),
    )

    def get_roles(self, user):
        role_name = dict(UserRelation.TYPE_CHOICES)
        roles = [role_name[relation.member_type] for relation in user.userrelation_set.all()]
        if user.is_superuser:
            roles = ['System Admin'] + roles
        elif user.is_super_admin:
            roles = ['Super Admin'] + roles
        return roles

    get_roles.short_description = "Role"

    def get_hosts(self, user):
        return [host.get_short_name() for host in user.hosts.all()]

    get_hosts.short_description = "Host"

    exclude = ()
    inlines = (UserRelationInlineModel,)

    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'username', 'email', 'date_of_birth', 'password1', 'password2'),
        },),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    filter_horizontal = ('hosts',)

    def get_fieldsets(self, request, obj=None):
        fieldset = super().get_fieldsets(request, obj)
        if request.user.is_super_admin:
            fieldset_dict = dict(fieldset)
            if 'Account' in fieldset_dict:
                if 'is_super_admin' not in fieldset_dict['Account']['fields']:
                    fieldset_dict['Account']['fields'] += ('is_super_admin',)
        else:
            fieldset_dict = dict(fieldset)
            if 'Account' in fieldset_dict:
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
        return exclude + ('bank',)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return fields

    def get_queryset(self, request):
        queryset = super().get_queryset(request).distinct()

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

    def has_add_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('add', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)

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


class TeamAdmin(MyAdmin):
    inlines = (TeamUserRelationInlineModel,)

    list_display = ('name', 'slug', 'host', 'get_member', 'rank')

    def get_member(self, team):
        return ", ".join([user.name() for user in team.member.all()])

    get_member.short_description = 'Team Member'


class FAQAdmin(MyAdmin):
    inlines = (QuestionAndAnswerInlineModel,)

    list_display = ('title', 'get_num_faq')

    def get_num_faq(self, faq):
        return faq.questionandanswer_set.count()

    get_num_faq.short_description = "Number of FAQs"


class HostAdmin(MyAdmin, ReverseModelAdmin):
    inlines = (JoinPageInlineModel, SocialMediaLinkInlineModel)
    inline_type = 'stacked'
    inline_reverse = ['address', 'bank']

    list_display = ('name', 'slug', 'email', 'founding_date', 'address')

    def get_readonly_fields(self, request, obj=None):
        readonly_field = super().get_readonly_fields(request, obj)
        if request.user.is_super_admin or request.user.is_superuser:
            return super().get_readonly_fields(request, obj)

        return readonly_field + ('slug', 'name', 'email')


class PartnerAdmin(MyAdmin, ReverseModelAdmin):
    inline_type = 'stacked'
    inline_reverse = ['address', ]

    list_display = ('name', 'address', 'logo')


class CycleDonationRelationInlineModel(PermissionInlineModel):
    model = CycleDonation.projects.through
    extra = 1



class PostAdmin(MyAdmin):

    ordering = ('-published', 'title',)
    search_fields = ('title', 'text')

    def get_author(self, post):
        if post.author:
            return post.author
        else:
            return post.author_str

    get_author.short_description = 'Author'

    class HostListFilter(admin.SimpleListFilter):
        title = 'Host'
        parameter_name = 'host'

        def lookups(self, request, model_admin):
            if request.user.is_super_admin:
                return [(host.slug, host.name) for host in Host.objects.all()]

            return [(host.slug, host.name) for host in request.user.hosts.all()]

        def queryset(self, request, queryset):
            if self.value():
                queryset = queryset.filter(host__slug=self.value())
            return queryset.distinct()

    def get_list_filter(self, request):
        if request.user.is_super_admin or request.user.is_superuser:
            return self.HostListFilter, 'published',
        else:
            return 'published',

    def get_list_display(self, request):
        if request.user.is_super_admin or request.user.is_superuser:
            return 'title', 'get_author', 'host', 'published',
        else:
            return 'title', 'get_author', 'published',


class ContactMessageAdmin(MyAdmin):
    search_fields = ('subject', 'message', 'email', 'name')

    class HostListFilter(admin.SimpleListFilter):
        title = 'Host'
        parameter_name = 'host'

        def lookups(self, request, model_admin):
            if request.user.is_super_admin:
                return [(host.slug, host.name) for host in Host.objects.all()]

            return [(host.slug, host.name) for host in request.user.hosts.all()]

        def queryset(self, request, queryset):
            if self.value():
                queryset = queryset.filter(host__slug=self.value())
            return queryset.distinct()

    def get_list_filter(self, request):
        if request.user.is_super_admin or request.user.is_superuser:
            return self.HostListFilter, 'reason', 'submission_date'
        else:
            return 'reason', 'submission_date'

    def get_list_display(self, request):
        if request.user.is_super_admin or request.user.is_superuser:
            return 'subject', 'name', 'email', 'reason', 'host', 'submission_date'
        else:
            return 'subject', 'name', 'email', 'reason', 'submission_date'


class ProjectAdmin(MyAdmin):
    inlines = (MilestoneInlineModel, )
    list_display = ('name', 'get_hosts', 'get_country', 'start_date', 'end_date', 'completed', 'published')

    def get_hosts(self, project):
        return ", ".join([host.name.replace("Weitblick ", "") for host in project.hosts.all()])

    def get_country(self, project):
        if project.location and project.location.country:
            return project.location.country.name
        else:
            return "-"

    get_country.short_description = 'Country'
    get_country.admin_order_field = 'location'
    get_hosts.short_description = 'Hosts'


class EventAdmin(MyAdmin):

    list_display = ('title', 'start', 'end', 'host')

    ordering = ('-start',)

    exclude = ('calendar', 'creator')

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'host') and request.user.hosts.count() == 1:
            obj.host = request.user.hosts.all()[0]

        try:
            calendar = Calendar.objects.get(slug=obj.host.slug)
        except Calendar.DoesNotExist:
            calendar = Calendar(name=obj.host.name, slug=obj.host.slug)
            calendar.save()
        obj.calendar = calendar
        if not obj.creator:
            obj.creator = request.user
        super().save_model(request, obj, form, change)


class AddressAdmin(MyAdmin):

    list_display = ('name', 'street', 'city', 'postal_code', 'get_country', )

    def get_country(self, address):
        return address.country.name
    get_country.short_description = 'Country'
    get_country.admin_order_field = 'country'


class CycleDonationAdmin(MyAdmin):
    inlines = (CycleDonationRelationInlineModel, )

    list_display = ('name', 'get_projects', 'partner', 'slug', 'rate_euro_km', 'goal_amount')

    def get_projects(self, cycle_donation):
        return ", ".join([project.name for project in cycle_donation.projects.all()])

    get_projects.short_description = 'Projects'


class DocumentAdmin(MyAdmin):

    list_display = ('title', 'host', 'document_type', 'published', 'public', 'valid_from')


class DonationAdmin(MyAdmin):

    list_display = ('host', 'project', 'amount', 'note')


class ContentAdmin(MyAdmin):

    list_display = ('type', 'host', )


class LocationAdmin(MyAdmin):

    list_display = ('name', 'street', 'postal_code', 'city', 'get_country', 'geolocation')

    def get_country(self, address):
        return address.country.name
    get_country.short_description = 'Country'
    get_country.admin_order_field = 'country'


class PhotoAdmin(MyAdmin):

    list_display = ('title', 'slug', 'type', 'uploader', 'host',)
    exclude = ('uploader', 'sites',)

    def save_model(self, request, obj, form, change):
        if not obj.uploader:
            obj.uploader = request.user

        if not obj.host and request.user.hosts.count() == 1:
            obj.host = request.user.hosts.all()[0]

        obj.save()


class BankAccountAdmin(MyAdmin):

    def get_queryset(self, request):
        if request.user.is_superuser or request.user.is_super_admin:
            return super().get_queryset(request)

        hosts = request.user.get_maintaining_hosts()
        if hosts:
            qs_hosts = BankAccount.objects.filter(host__in=hosts)
            qs_users = BankAccount.objects.filter(userrelation__host__in=hosts)
            return qs_hosts + qs_users

        return BankAccount.objects.filter(userrelation__user=request.user)

# since we're not using Django's built-in permissions,
# register our own user model and unregister the Group model from admin.
try:
    admin.site.register(User, UserAdmin)
except admin.sites.AlreadyRegistered:
    admin.site.unregister(User)
    admin.site.register(User, UserAdmin)


admin.site.unregister(Group)
admin.site.register(Address, AddressAdmin)
admin.site.register(BlogPost, PostAdmin)
admin.site.register(BankAccount, MyAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(CycleDonation, CycleDonationAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Donation, DonationAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(NewsPost, PostAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Photo, PhotoAdmin)
