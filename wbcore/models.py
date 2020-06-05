import os
import slugify
from django.db import models, transaction
from django.dispatch import receiver
from django_countries.fields import CountryField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib.auth.models import PermissionsMixin, BaseUserManager, AbstractBaseUser
from photologue.models import Gallery as PhotologueGallery, Photo as PhotologuePhoto
from os.path import splitext
from localflavor.generic.models import IBANField, BICField
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from django.urls import reverse
from django_google_maps import fields as map_fields
from schedule.models.events import Event as ScheduleEvent, Calendar
from form_designer.models import Form as EventForm
from wbcore import predicates as pred
from wbcore.storage import OverwriteStorage
from rules.contrib.models import RulesModel, RulesModelBase, RulesModelMixin
from sortedm2m.fields import SortedManyToManyField
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
import rules, datetime


class Photo(RulesModelMixin, PhotologuePhoto, metaclass=RulesModelBase):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    TYPE_CHOICES = (
        ('header', 'Header'),
        ('project', 'Project'),
        ('event', 'Event'),
        ('blog', 'Blog'),
        ('news', 'News'),
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True)
    uploader = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    host = models.ForeignKey('Host', on_delete=models.SET_NULL, null=True)

    def get_hosts(self):
        return self.host


class Address(models.Model):
    name = models.CharField(max_length=200)
    country = CountryField()
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=30)
    state = models.CharField(max_length=30, null=True, blank=True)
    street = models.CharField(max_length=30)

    def belongs_to_host(self, host):
        return

    def __str__(self):
        return ", ".join(filter(None, [self.name, self.street, self.postal_code, self.city, self.country.name]))


class Location(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(blank=True, null=True,max_length=300 )
    country = CountryField()
    postal_code = models.CharField(blank=True, null=True, max_length=20)
    city = models.CharField(blank=True, null=True, max_length=30)
    state = models.CharField(blank=True, null=True, max_length=30)
    street = models.CharField(blank=True, null=True, max_length=30)
    address = map_fields.AddressField(max_length=200, null=True)
    geolocation = map_fields.GeoLocationField(max_length=100, null=True)
    map_zoom = models.FloatField(default=14)

    def belongs_to_host(self, host):
        return True

    def lat(self):
        return self.geolocation.lat

    def lng(self):
        return self.geolocation.lon

    def __str__(self):
        return self.name + " (" + self.country.name + ")"


class Host(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin,
            "delete": pred.is_super_admin,
        }

    slug = models.SlugField(primary_key=True, max_length=50, unique=True)
    name = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    charter_name = models.CharField(max_length=100, blank=False, null=True, help_text="Name des Vereins laut Satzung")
    founding_date = models.DateField(help_text="Gründungsdatum des Vereins")
    tax_exemption_notice_date = models.DateField(null=True, blank=False, help_text="Datum des letzten gültigen Freistellungsbescheid")
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True)
    location = models.OneToOneField(Location, on_delete=models.SET_NULL, null=True)
    partners = SortedManyToManyField('Partner', blank=True, related_name='hosts')
    bank = models.OneToOneField('BankAccount', on_delete=models.SET_NULL, null=True)

    def belongs_to_host(self, host):
        return host == self

    def search_title(self):
        return self.name

    def search_url(self):
        return reverse('host', args=[self.slug])

    def search_image(self):
        return ""

    def get_short_name(self):
        return self.name.replace("Weitblick ", "").replace(" e.V.", "")

    @staticmethod
    def get_model_name():
        return "Union"

    def __str__(self):
        return self.name

    def get_hosts(self):
        return self

    def instagram(self):
        sm = self.socialmedialink_set.filter(type='instagram').all()
        link = None
        if len(sm):
            link = sm[0].link
        
        if link:
            name = link.replace("https://www.instagram.com/", "")
            name = name.replace("/", "")
            return name
        return None


class SocialMediaLink(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    CHOICES = (
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter'),
    )

    type = models.CharField(max_length=20, choices=CHOICES, blank=False)
    link = models.URLField()
    host = models.ForeignKey(Host, on_delete=models.CASCADE, null=True)

    def belongs_to_host(self, host):
        return self.host is host

    def __str__(self):
        return dict(self.CHOICES)[self.type]

    def get_hosts(self):
        return [self.host]


class JoinPage(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin,
            "view": pred.is_super_admin | pred.is_admin,
            "change": pred.is_super_admin | pred.is_admin,
            "delete": pred.is_super_admin,
        }

    enable_form = models.BooleanField(default=False)
    text = models.TextField()
    image = models.OneToOneField(Photo, on_delete=models.SET_NULL, null=True, blank=True)
    sepa_text = models.TextField()
    min_fee = models.IntegerField()
    max_fee = models.IntegerField()
    host = models.OneToOneField(Host, on_delete=models.CASCADE, null=True)

    def get_hosts(self):
        return [self.host]


class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, date_of_birth, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        if not first_name:
            raise ValueError('Users must have a first name')

        if not last_name:
            raise ValueError('Users must have a last name')

        if not username:
            raise ValueError('Users must have a user name')

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=self.normalize_email(email),
            date_of_birth=date_of_birth,
            is_active=True
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, username, email, date_of_birth, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
            date_of_birth=date_of_birth,
        )
        user.is_superuser = True
        user.is_super_admin = True
        user.save(using=self._db)
        return user


def user_image_path(user, filename):
    extension = os.path.splitext(filename)[1]
    extension = extension.lower().replace("jpeg", "jpg")
    return 'images/users/%s%s' % (user.pk, extension)


class User(AbstractBaseUser, PermissionsMixin, RulesModelMixin, metaclass=RulesModelBase):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin,
            "view": pred.is_super_admin | pred.is_admin | pred.is_self,
            "change": pred.is_super_admin | pred.is_admin | pred.is_self,
            "delete": pred.is_super_admin,
        }

    username = models.CharField(max_length=60)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)

    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    date_of_birth = models.DateField(null=True)
    is_active = models.BooleanField(default=True)

    @property
    def is_staff(self):
        return True

    is_super_admin = models.BooleanField(default=False)

    def get_hosts_for_role(self, role):
        if isinstance(role, (list, QuerySet)):
            admin_relations = self.userrelation_set.filter(member_type__in=role).all()
        else:
            admin_relations = self.userrelation_set.filter(member_type=role).all()
        return [relation.host for relation in admin_relations]

    def get_maintaining_hosts(self):
        return self.get_hosts_for_role('admin')

    def get_hosts_for_admin(self):
        return self.get_hosts_for_role('admin')

    def get_hosts_for_editor(self):
        return self.get_hosts_for_role('editor')

    def get_hosts_for_author(self):
        return self.get_hosts_for_role('author')

    def get_hosts_for_member(self):
        return self.get_hosts_for_role('member')

    def has_role_for_host(self, member_type, host):
        if isinstance(member_type, (list, QuerySet)) and isinstance(host, (list, QuerySet)):
            return self.userrelation_set.filter(member_type__in=member_type, host__in=host).count() > 0
        elif isinstance(member_type, (list, QuerySet)):
            return self.userrelation_set.filter(member_type__in=member_type, host=host).count() > 0
        elif isinstance(host, (list, QuerySet)):
            return self.userrelation_set.filter(member_type=member_type, host__in=host).count() > 0
        else:
            return self.userrelation_set.filter(member_type=member_type, host=host).count() > 0

    def is_admin_of_host(self, host):
        return self.has_role_for_host('admin', host)

    def is_editor_of_host(self, host):
        return self.has_role_for_host('editor', host)

    def is_author_of_host(self, host):
        return self.has_role_for_host('author', host)

    def is_member_of_host(self, host):
        return self.has_role_for_host('member', host)

    def has_role(self, role):
        return self.userrelation_set.filter(member_type=role).count() > 0

    def role(self):
        roles = dict(UserRelation.TYPE_CHOICES)
        return [roles[member.member_type] for member in self.userrelation_set.all()]

    hosts = models.ManyToManyField(Host, through='UserRelation')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'date_of_birth']

    def has_perm(self, perm, obj=None):
        if 'schedule.delete_event' == perm and obj is None:
          return True
        elif 'photologue.delete_photo' == perm and obj is None:
          return True

        return super(User, self).has_perm(perm, obj)

    def has_module_perms(self, app_label):
        # only allow super admins to see the modules beside wbcore.

        if self.is_super_admin:
            return True

        if app_label is 'wbcore':
            return True

        return False

    def name(self):
        if self.first_name and self.last_name:
            return self.first_name + " " + self.last_name
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        elif self.username:
            return self.username
        else:
            return ""

    name.admin_order_field = 'first_name'

    image = models.ImageField(null=True, blank=True, storage=OverwriteStorage(), upload_to=user_image_path)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True, blank=True)
    since = models.DateField(auto_now_add=True)
    until = models.DateField(null=True, blank=True)
    bank = models.OneToOneField('BankAccount', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        name = self.name()
        if name:
            return self.name() + ", " + self.email
        else:
            return self.email

    def belongs_to_host(self, host):
        return host in self.hosts.all()

    def get_hosts(self):
        return self.hosts.all()


class Content(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin,
            "view": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "delete": pred.is_super_admin,
        }

    TYPE_CHOICES = (
        ('welcome', 'Welcome'),
        ('about', 'About'),
        ('idea', 'Idea'),
        ('history', 'History'),
        ('teams', 'Teams'),
        ('contact', 'Contact'),
        ('charter', 'Charter'),
        ('reports', 'Reports'),
        ('donate', 'Donate'),
        ('join', 'Join'),
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True)
    host = models.ForeignKey(Host, on_delete=models.CASCADE, null=False)
    text = models.TextField()
    image = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL)

    def belongs_to_host(self, host):
        return host.slug == self.host.slug

    def validate_unique(self, *args, **kwargs):
        super(Content, self).validate_unique(*args, **kwargs)

        if self._state.adding and Content.objects.filter(host=self.host, type=self.type).exists():

            msg = 'The content for ' + dict(self.TYPE_CHOICES)[self.type] + ' already exist!'

            raise ValidationError(msg,
                {
                    NON_FIELD_ERRORS: [msg],
                }
            )

    def __str__(self):
        return dict(self.TYPE_CHOICES)[self.type] + " (" + self.host.name + ")"

    def get_hosts(self):
        return [self.host]


def save_partner_logo(instance, filename):
    path = "partners/" + instance.name.lower().replace(' ', '_') + splitext(filename)[1].lower()
    return replace_umlaute(path)


class Partner(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "delete": pred.is_super_admin | pred.is_admin | pred.is_editor,
        }

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=50, unique=True, null=True)
    description = models.TextField()
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, blank=True, null=True)
    logo = models.ImageField(upload_to=save_partner_logo, null=True, blank=True)
    link = models.URLField(blank=True)

    CATEGORY_CHOICES = (
        ('project', _('Project Partner')),
        ('sponsor', _('Sponsor')),
        ('patron', _('Patron')),
        ('network', _('Network'))
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    active = models.BooleanField(default=True, help_text='If this is not selected, the partnership will be displayed as concluded')
    public = models.BooleanField(default=True, help_text='If this is not selected, the partner will not be displayed.')

    def belongs_to_host(self, host):
        return True

    def __str__(self):
        return self.name

    def get_hosts(self):
        return Host.objects.all()


class Project(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True, null=True)
    hosts = models.ManyToManyField(Host, related_name="projects")
    short_description = models.TextField()
    description = models.TextField()
    image = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    partners = SortedManyToManyField(Partner, blank=True, related_name='projects')

    donation_goal = models.DecimalField(max_digits=11, decimal_places=2, null=True, blank=True)
    goal_description = models.CharField(max_length=500, blank=True)
    donation_account = models.OneToOneField('BankAccount', on_delete=models.SET_NULL, null=True, blank=True)
    donation_current = models.DecimalField(max_digits=11, decimal_places=2, null=True, blank=True)

    photos = SortedManyToManyField(Photo, related_name='projects', verbose_name=_('photos'), blank=True)
    completed = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    priority = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def belongs_to_host(self, host):
        return host in self.hosts.all()

    @staticmethod
    def get_model_name():
        return 'Project'

    def host_name_list(self):
        host_names = [host.name for host in self.hosts.all()]
        return ", ".join(host_names)

    def __str__(self):
        return self.name

    def get_title_image(self):
        if self.image:
            return self.image
        elif self.photos.all():
            return self.photos.all()[0]
        return None

    def get_hosts(self):
        return self.hosts.all()
    
    def search_title(self):
        return self.name

    def search_url(self):
        return reverse('project', args=[self.slug])

    def search_image(self):
        image = self.get_title_image()
        return image.get_search_mini_url() if image else None


class Event(RulesModelMixin, ScheduleEvent, metaclass=RulesModelBase):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "delete": pred.is_super_admin | pred.is_admin | pred.is_editor,
        }
        get_latest_by = ['start']

    slug = models.SlugField(max_length=50, unique=True, null=True)
    teaser = models.TextField(max_length=120, blank=True)
    projects = models.ManyToManyField(Project, blank=True, related_name='events')
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    image = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL)
    photos = SortedManyToManyField(Photo, related_name='events', verbose_name=_('photos'), blank=True)
    form = models.OneToOneField(EventForm, null=True, blank=True, on_delete=models.SET_NULL)
    cost = models.CharField(max_length=50, blank=True, default="")

    def get_title_image(self):
        if self.image:
            return self.image
        elif self.photos.all():
            return self.photos.all()[0]
        return None

    def search_title(self):
        return self.title

    def search_url(self):
        return reverse('event', args=[self.slug])

    def search_image(self):
        image = self.get_title_image()
        return image.get_search_mini_url() if image else None

    @staticmethod
    def get_model_name():
        return 'Event'

    def belongs_to_host(self, host):
        return self.host == host

    def get_hosts(self):
        return [self.host]


class UserRelation(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin,
            "view": pred.is_super_admin | pred.is_admin,
            "change": pred.is_super_admin | pred.is_admin,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('editor', 'Editor'),
        ('author', 'Author'),
        ('member', 'Member'),
        ('applicant', 'Applicant'),
    )
    member_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='applicant')
    membership_fee = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(2), MaxValueValidator(30)])

    def __str__(self):
        return str(self.user) + " in " + self.host.name + " as " + dict(self.TYPE_CHOICES)[self.member_type]

    def belongs_to_host(self, host):
        return self.host == host

    def get_hosts(self):
        return [self.host]


class NewsPost(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_editor | pred.is_author,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor | pred.is_author,
            "delete": pred.is_super_admin | pred.is_admin | pred.is_editor | pred.is_author,
        }
        get_latest_by = 'published'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, null=False, blank=False, unique=True)
    text = models.TextField()
    image = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL)
    added = models.DateTimeField(blank=True, null=True)
    updated = models.DateTimeField(blank=True, null=True, auto_now=True)
    published = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    priority = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)
    RANGE_CHOICES = (
        ('preview', 'Preview'),
        ('hidden', 'Hidden'),
        ('global', 'Global'),
        ('federal', 'Federal'),
        ('city', 'City')
    )
    range = models.CharField(max_length=20, choices=RANGE_CHOICES, default='preview', null=True)
    teaser = models.TextField()
    host = models.ForeignKey(Host, to_field='slug', on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="news")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_str = models.CharField(max_length=200, null=True, blank=True)
    photos = SortedManyToManyField(Photo, related_name='news_posts', verbose_name=_('photos'), blank=True)

    current_host = None

    def save(self, **kwargs):
        super().save(**kwargs)

    def get_hosts(self):
        return [self.host]

    def belongs_to_host(self, host):
        return self.host == host

    def link(self):
        args = [self.current_host.slug, self.pk] if self.current_host else [self.pk]
        return reverse('news-post', args=args)

    def get_title_image(self):
        if self.image:
            return self.image
        elif self.photos.all():
            return self.photos.all()[0]
        return None

    def search_title(self):
        return self.title

    def search_url(self):
        return reverse('news-post', args=[self.pk])

    def search_image(self):
        image = self.get_title_image()
        return image.get_search_mini_url() if image else None

    @staticmethod
    def get_model_name():
        return 'News'

    def author_name(self):
        name = self.author_str
        if self.author:
            name = self.author.first_name + " " + self.author.last_name
        return name

    def __str__(self):
        city = (" (" + self.host.name + ")") if self.host else ''
        return self.title + city


class BlogPost(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_editor | pred.is_author,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor | pred.is_author,
            "delete": pred.is_super_admin | pred.is_admin | pred.is_editor | pred.is_author,
        }
        get_latest_by = 'published'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, null=False, blank=False, unique=True)
    text = models.TextField()
    image = models.ForeignKey(Photo, null=True, blank =True, on_delete=models.SET_NULL)
    added = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    priority = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)
    RANGE_CHOICES = (
        ('preview', 'Preview'),
        ('hidden', 'Hidden'),
        ('global', 'Global'),
        ('federal', 'Federal'),
        ('city', 'City')
    )
    range = models.CharField(max_length=20, choices=RANGE_CHOICES, default='preview', null=True)
    teaser = models.TextField()
    host = models.ForeignKey(Host, to_field='slug', on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="blog")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_str = models.CharField(max_length=200, null=True, blank=True)
    photos = SortedManyToManyField(Photo, related_name='blog_posts', verbose_name=_('photos'), blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)

    def belongs_to_host(self, host):
        return self.host == host

    def search_title(self):
        return self.title_de

    def search_url(self):
        return reverse('blog-post', args=[self.pk])

    def get_title_image(self):
        if self.image:
            return self.image
        elif self.photos.all():
            return self.photos.all()[0]
        return None

    def search_image(self):
        image = self.get_title_image()
        return image.get_search_mini_url() if image else None

    def placeholder(self):
        return 'Post'

    @staticmethod
    def get_model_name():
        return 'Blog'

    def author_name(self):
        name = self.author_str
        if self.author:
            name = self.author.first_name + " " + self.author.last_name
        return name

    def __str__(self):
        city = ("(" + self.host.city + ")") if self.host else ''
        return self.title + " " + city

    def get_hosts(self):
        return [self.host]

def replace_umlaute(string):
    string_utf8 = string.replace('ä', 'ae').replace('ü', 'ue').replace('ö', 'oe').replace('ß', 'ss')
    # get rid of other utf8 symbols
    string_ascii = string_utf8.encode("utf-8").decode("ascii", "ignore")
    return string_ascii

def save_document(instance, filename):
    path = "documents/" + instance.host.slug + "/" + instance.title.lower().replace(' ', '_') + splitext(filename)[1].lower()
    return replace_umlaute(path)


class Document(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "view": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "delete": pred.is_super_admin | pred.is_admin | pred.is_editor,
        }
        get_latest_by = 'valid_from'

    title = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to=save_document)
    host = models.ForeignKey(Host, on_delete=models.SET_NULL, null=True)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    TYPE_CHOICES = (
        ('financial_report', 'Financial Report'),
        ('annual_report', 'Annual Report'),
        ('charter', 'Charter'),
        ('membership_declaration', 'Membership Declaration'),
        ('other', 'Other')
    )
    document_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default='financial_report', null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    valid_from = models.DateField(blank=False, default=datetime.date.today)
    public = models.BooleanField(default=True)

    def belongs_to_host(self, host):
        return self.host == host

    def __str__(self):
        city = ("(" + self.host.city + ")") if self.host else ''
        return self.title + " " + city

    def get_hosts(self):
        return [self.host]


class Team(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin,
            "delete": pred.is_super_admin | pred.is_admin,
        }
        ordering = ['rank', 'name']

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, null=False, blank=False, unique=True)
    teaser = models.TextField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    host = models.ForeignKey(Host, on_delete=models.CASCADE, null=True)
    member = models.ManyToManyField(User, through='TeamUserRelation')
    image = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    rank = models.IntegerField(default=99)

    def belongs_to_host(self, host):
        return self.host == host

    def search_title(self):
        return self.name

    def search_url(self):
        return reverse('team', args=[self.slug])

    def search_image(self):
        image = self.image
        return image.get_search_mini_url() if image else None

    @staticmethod
    def get_model_name():
        return "Team"

    def __str__(self):
        return self.name + " (" + self.host.name + ")"

    def validate_unique(self, *args, **kwargs):
        super(Team, self).validate_unique(*args, **kwargs)

        same_host_and_slug = Team.objects.filter(host=self.host, slug=self.slug)

        if same_host_and_slug.exists() and (self not in same_host_and_slug):  # second part is necessary to be able to edit a team. Otherwise saving after editing will raise slug already exists error
            raise ValidationError(
                {
                    NON_FIELD_ERRORS: [
                        'The \"slug\" ' + self.slug + ' already exist!',
                    ],
                }
            )

    def get_hosts(self):
        return [self.host]


class TeamUserRelation(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    text = models.TextField()
    role = models.TextField(blank=True, default="")
    email = models.EmailField(max_length=100, blank=True, default="")
    priority = models.IntegerField(default=99)

    def belongs_to_host(self, host):
        return self.team.host == host

    def __str__(self):
        return self.user.name() + ' in ' + self.team.name

    def get_hosts(self):
        return self.team.get_hosts() if self.team else []


class Donation(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin,
            "view": pred.is_super_admin | pred.is_admin,
            "change": pred.is_super_admin | pred.is_admin,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    host = models.ForeignKey(Host, on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    date = models.DateField(null=True, blank=False)
    major_donation = models.BooleanField(default=False, null=False, blank=False)
    donator_name = models.CharField(max_length=100, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    def belongs_to_host(self, host):
        return self.host == host

    def __str__(self):
        project = ("(" + self.project.name + ")") if self.project else ''
        return str(self.amount) + "€ für " + self.host.city + project

    def get_hosts(self):
        return [self.host]


class Milestone(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "view": rules.always_allow,
            "change": pred.is_super_admin | pred.is_admin | pred.is_editor,
            "delete": pred.is_super_admin | pred.is_admin | pred.is_editor,
        }
        ordering = ('date', )

    project = models.ForeignKey(Project, related_name='milestones', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField()
    date = models.DateField(blank=True)
    reached = models.BooleanField()

    def __str__(self):
        return self.name

    def belongs_to_host(self, host):
        return self.project.belongs_to_host(host)

    def get_hosts(self):
        return self.project.get_hosts() if self.project else []


class BankAccount(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin | pred.is_admin | pred.is_author | pred.is_editor | pred.is_member,
            "view": pred.is_super_admin | pred.is_admin | pred.is_user_of_bank_account,
            "change": pred.is_super_admin | pred.is_admin | pred.is_user_of_bank_account,
            "delete": pred.is_super_admin,
        }

    account_holder = models.CharField(max_length=100)
    iban = IBANField(include_countries=IBAN_SEPA_COUNTRIES)
    bic = BICField()

    def belongs_to_host(self, host):
        if hasattr(self, 'host') and self.host == host:
            return True
        elif hasattr(self, 'user') and self.user.host == host:
            return True
        else:
            return False

    def type(self):
        if hasattr(self, 'host'):
            return 'host'
        if hasattr(self, 'user'):
            return 'user'

    def __str__(self):
        return self.account_holder

    def get_hosts(self):
        if self.host:
            return self.host
        elif self.user:
            return self.user.hosts
        else:
            return None


class ContactMessage(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin,
            "view": pred.is_super_admin | pred.is_admin,
            "change": pred.is_super_admin,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    REASON_CHOICES = (
        ('donation', _('Donation')),
        ('membership', _('Membership')),
        ('other', _('Other'))
    )
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=100)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    submission_date = models.DateTimeField(auto_now_add=True)

    def belongs_to_host(self, host):
        return host == self.host

    def get_hosts(self):
        return [self.host]

    def __str__(self):
        return "%s (%s)" % (self.subject, self.name)


class CycleDonationRelation(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin,
            "view": pred.is_super_admin | pred.is_admin,
            "change": pred.is_super_admin,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    cycle_donation = models.ForeignKey('CycleDonation', on_delete=models.CASCADE)
    current_amount = models.FloatField(default=0)
    goal_amount = models.FloatField(null=True, blank=True, default=None)
    finished = models.BooleanField(default=False)
    current_km = models.FloatField(default=0)
    users = models.ManyToManyField(User, null=True, blank=True)

    @classmethod
    def add_segment(cls, id, distance, user):
        # TODO check for sum of all donations -> set finish
        with transaction.atomic():
            donation_relation = cls.objects.select_for_update().get(id=id)
            goal_amount = donation_relation.goal_amount \
                if donation_relation.goal_amount else donation_relation.cycle_donation.goal_amount
            if donation_relation.finished and goal_amount == donation_relation.current_amount:
                return 0

            amount = distance * donation_relation.cycle_donation.rate_euro_km
            new_amount = donation_relation.current_amount + amount
            if new_amount >= goal_amount:
                donation_relation.current_amount = goal_amount
                donation_relation.finished = True

            else:
                donation_relation.current_amount = new_amount
                donation_relation.finished = False

            donation_relation.current_km + distance
            donation_relation.users.add(user)
            donation_relation.save()
            return amount

    def __str__(self):
        return self.project.name


class CycleDonation(RulesModel):
    class Meta:
        rules_permissions = {
            "add": pred.is_super_admin,
            "view": pred.is_super_admin | pred.is_admin,
            "change": pred.is_super_admin,
            "delete": pred.is_super_admin | pred.is_admin,
        }

    projects = models.ManyToManyField(Project, through=CycleDonationRelation)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True)
    logo = models.ImageField()
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True)
    goal_amount = models.FloatField(null=False, blank=False)
    rate_euro_km = models.FloatField()  # euro per km, e.g. 0.1 per km (10 cents per km)

    def current_amount(self):
        current_amount = 0
        for relation in self.cycledonationrelation_set:
            current_amount += relation.current_amount
        return current_amount

    def __str__(self):
        return self.name


class CycleTour(RulesModel):
    class Meta:
        rules_permissions = {
            "add": rules.is_superuser,
            "view": rules.is_superuser,
            "change": rules.is_superuser,
            "delete": rules.is_superuser,
        }

    index = models.IntegerField(default=-1)
    donations = models.ManyToManyField(CycleDonation)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    finished = models.BooleanField(default=False)
    km = models.FloatField(default=0)
    euro = models.FloatField(default=0)

    @property
    def start(self):
        seg = self.cyclesegment_set.first()
        if seg:
            return seg.start
        return None

    @property
    def end(self):
        seg = self.cyclesegment_set.last()
        if seg:
            return seg.end
        return None

    @property
    def duration(self):
        start = self.start
        end = self.end
        if start and end:
            return self.end - self.start
        return False

    def __str__(self):
        return "Tour %s of user %s" % (self.index, self.user.name())


class CycleSegment(RulesModel):
    class Meta:
        rules_permissions = {
            "add": rules.is_superuser,
            "view": rules.is_superuser,
            "change": rules.is_superuser,
            "delete": rules.is_superuser,
        }

    start = models.DateTimeField()
    end = models.DateTimeField()
    distance = models.FloatField()
    tour = models.ForeignKey(CycleTour, on_delete=models.CASCADE)

    def save(self, **kwargs):
        super().save(**kwargs)
        project = self.tour.project
        user = self.tour.user
        self.tour.km += self.distance

        for cycle_relation in project.cycledonationrelation_set.all():
            self.tour.euro += cycle_relation.add_segment(cycle_relation.pk, self.distance, user)
        self.tour.save()

    def get_cycle_donations(self):
        return self.tour.project.cycledonation_set.all()

    def __str__(self):
        return "Cycle segment %s of tour %s of user %s" % (self.pk, self.tour.index, self.tour.user.name())


class FAQ(RulesModel):
    class Meta:
        rules_permissions = {
            "add": rules.is_superuser | pred.is_super_admin,
            "view": rules.is_superuser | pred.is_super_admin,
            "change": rules.is_superuser | pred.is_super_admin,
            "delete": rules.is_superuser | pred.is_super_admin
        }

    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class QuestionAndAnswer(RulesModel):
    class Meta:
        rules_permissions = {
            "add": rules.is_superuser | pred.is_super_admin,
            "view": rules.is_superuser | pred.is_super_admin,
            "change": rules.is_superuser | pred.is_super_admin,
            "delete": rules.is_superuser | pred.is_super_admin
        }

    question = models.CharField(max_length=300)
    answer = models.TextField()
    faq = models.ForeignKey(FAQ, on_delete=models.CASCADE)

    def __str__(self):
        return self.question
    
    
@receiver(models.signals.post_delete, sender=Photo)
def auto_delete_photo_file_on_delete(sender, instance, **kwargs):
    """
    Deletes image file from filesystem
    when corresponding `Photo` object is deleted.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

