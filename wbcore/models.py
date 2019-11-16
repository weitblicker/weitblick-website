from django.db import models
from django_countries.fields import CountryField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib.auth.models import (
    PermissionsMixin, BaseUserManager, AbstractBaseUser
)
from photologue.models import Gallery, Photo
from os.path import splitext
from localflavor.generic.models import IBANField, BICField
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from django.urls import reverse
from django_google_maps import fields as map_fields
from schedule.models.events import Event as ScheduleEvent
from form_designer.models import Form as EventForm
from django.contrib import messages


class Address(models.Model):
    name = models.CharField(max_length=200)
    country = CountryField()
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=30)
    state = models.CharField(max_length=30, null=True, blank=True)
    street = models.CharField(max_length=30)

    def belongs_to_host(self, host):
        return True

    def __str__(self):
        return ", ".join(filter(None, [self.name, self.street, self.postal_code, self.city, self.country.name]))


class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(blank=True, null=True,max_length=300 )
    country = CountryField()
    postal_code = models.CharField(blank=True, null=True, max_length=20)
    city = models.CharField(blank=True, null=True, max_length=30)
    state = models.CharField(blank=True, null=True, max_length=30)
    street = models.CharField(blank=True, null=True, max_length=30)
    address = map_fields.AddressField(max_length=200, null=True)
    geolocation = map_fields.GeoLocationField(max_length=100, null=True)

    def belongs_to_host(self, host):
        return True

    def lat(self):
        return self.geolocation.lat

    def lng(self):
        return self.geolocation.lon

    def __str__(self):
        return self.name + " (" + self.country.name + ")"


class Host(models.Model):
    slug = models.SlugField(primary_key=True, max_length=50, unique=True)
    name = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    founding_date = models.DateField()
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)

    def belongs_to_host(self, host):
        return host == self

    def search_title(self):
        return self.name

    def search_url(self):
        return reverse('host', args=[self.slug])

    def search_image(self):
        return ""

    @staticmethod
    def get_model_name():
        return "Union"

    def __str__(self):
        return self.name


class SocialMediaLink(models.Model):
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


class JoinPage(models.Model):
    enable_form = models.BooleanField(default=False)
    text = models.TextField()
    image = models.OneToOneField(Photo, on_delete=models.SET_NULL, null=True)
    sepa_text = models.TextField()
    min_fee = models.IntegerField()
    max_fee = models.IntegerField()
    host = models.OneToOneField(Host, on_delete=models.CASCADE, null=True)


class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, date_of_birth, password=None):
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

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email),
            date_of_birth=date_of_birth,
            is_active=True
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, date_of_birth, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            date_of_birth=date_of_birth,
        )
        user.is_super_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
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
        return True;

    is_super_admin = models.BooleanField(default=False)

    def get_maintaining_hosts(self):
        admin_relations = self.userrelation_set.filter(member_type='admin').all()
        return [relation.host for relation in admin_relations]

    def is_admin_of_host(self, host):
        return host in self.get_maintaining_hosts()

    def role(self):
        roles =dict(UserRelation.TYPE_CHOICES)
        return [roles[member.member_type] for member in self.userrelation_set.all()]

    hosts = models.ManyToManyField(Host, through='UserRelation')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'date_of_birth']

    def has_perm(self, perm, obj=None):
        # Does the user have a specific permission?
        if obj:
            print("has perm:", perm, obj)

        # admins have all rights
        if self.is_super_admin:
            return True

        if not obj:
            return True

        if perm.startswith("wbcore.view"):
            return True

        # Get all host objects where the user is an admin
        # If the object belongs to any of these hosts the
        # user has the right to access it
        for host in self.userrelation_set.filter(member_type='admin'):

            print("test", obj, self)

            if obj.belongs_to_host(host):
                if isinstance(obj, User):
                    if obj.is_super_admin:
                        return False
                    if obj.userrelation_set.get(member_type='admin'):
                        return False

                return True

        return False

    def has_module_perms(self, app_label):
        return True

    def name(self):
        return self.first_name + " " + self.last_name

    name.admin_order_field = 'first_name'

    image = models.ImageField(null=True, blank=True)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True, blank=True)
    since = models.DateField(auto_now_add=True)
    until = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name()

    def belongs_to_host(self, host):
        return host in self.hosts.all()


class Content(models.Model):
    TYPE_CHOICES = (
        ('welcome', 'Welcome'),
        ('about', 'About'),
        ('idea', 'Idea'),
        ('history', 'History'),
        ('teams', 'Teams'),
        ('contact', 'Contact'),
        ('transparency', 'Transparency'),
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


def save_partner_logo(instance, filename):
    return "partners/" + instance.name.lower().replace(' ', '_') + splitext(filename)[1].lower()


class Partner(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, blank=True, null=True)
    logo = models.ImageField(upload_to=save_partner_logo, null=True, blank=True)

    def belongs_to_host(self, host):
        return True

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True, null=True)
    hosts = models.ManyToManyField(Host)
    short_description = models.TextField()
    description = models.TextField()
    title_image = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)
    donation_goal = models.DecimalField(max_digits=11, decimal_places=2, null=True, blank=True)
    donation_current = models.DecimalField(max_digits=11, decimal_places=2, null=True, blank=True)
    gallery = models.ForeignKey(Gallery, blank=True, null=True, on_delete=models.SET_NULL)
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
        if self.title_image:
            return self.title_image
        elif self.gallery:
            return self.gallery.photos.first()
        else:
            return None


class Event(ScheduleEvent):
    slug = models.SlugField(max_length=50, unique=True, null=True)
    teaser = models.TextField(max_length=120, blank=True)
    projects = models.ManyToManyField(Project, blank=True)
    host = models.ManyToManyField(Host)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    image = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL)
    gallery = models.ForeignKey(Gallery, null=True, blank=True,on_delete=models.SET_NULL)
    form = models.OneToOneField(EventForm, null=True, blank=True, on_delete=models.SET_NULL)
    cost = models.CharField(max_length=50, blank=True, default="")

    def search_title(self):
        return self.title

    def search_url(self):
        return reverse('event', args=[self.slug])

    def search_image(self):
        # TODO: return first image of gallery instead, if no image is set
        return self.image.get_search_mini_url() if self.image else ""

    @staticmethod
    def get_model_name():
        return 'Event'

    def get_title_image(self):
        if self.image:
            return self.image
        elif self.gallery:
            return self.gallery.photos.first()
        else:
            return None

    class Meta:
        get_latest_by = ['start']

    def belongs_to_host(self, host):
        return self.host == host


class UserRelation(models.Model):
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
        print("member type", self.member_type, self.user)
        return str(self.user) + " in " + self.host.name + " as " + dict(self.TYPE_CHOICES)[self.member_type]

    def belongs_to_host(self, host):
        return self.host == host


class NewsPost(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    image = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL)
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
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_str = models.CharField(max_length=200, null=True, blank=True)
    gallery = models.ForeignKey(Gallery, null=True, blank =True, on_delete=models.SET_NULL)

    current_host = None

    def hosts(self):
        return [self.host]

    def belongs_to_host(self, host):
        return self.host == host

    def link(self):
        args = [self.current_host.slug, self.pk] if self.current_host else [self.pk]
        return reverse('news-post', args=args)

    def search_title(self):
        return self.title

    def search_url(self):
        return reverse('news-post', args=[self.pk])

    def search_image(self):
        return self.image.get_search_mini_url() if self.image else ""

    @staticmethod
    def get_model_name():
        return 'News'

    def author_name(self):
        name = self.author_str
        if self.author:
            name = self.author.first_name + " " + self.author.last_name
        return name

    class Meta:
        get_latest_by = 'published'

    def __str__(self):
        city = (" (" + self.host.name + ")") if self.host else ''
        return self.title + city


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
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
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_str = models.CharField(max_length=200, null=True, blank=True)
    gallery = models.ForeignKey(Gallery, null=True, blank =True, on_delete=models.SET_NULL)

    def belongs_to_host(self, host):
        return self.host == host

    def search_title(self):
        return self.title_de

    def search_url(self):
        return reverse('blog-post', args=[self.pk])

    def search_image(self):
        return self.image.get_search_mini_url() if self.image else ""

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

    class Meta:
        get_latest_by = 'published'

    def __str__(self):
        city = ("(" + self.host.city + ")") if self.host else ''
        return self.title + " " + city


def save_document(instance, filename):
    return "documents/"+ instance.host.slug +"/" + instance.title.lower().replace(' ', '_') + splitext(filename)[1].lower()


class Document(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to=save_document)
    host = models.ForeignKey(Host, on_delete=models.SET_NULL, null=True)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    TYPE_CHOICES = (
        ('financial_report', 'Finanical Report'),
        ('annual_report', 'Annual Report'),
        ('charter', 'Charter'),
        ('membership_declaration', 'Membership Declaration'),
        ('other', 'Other')
    )
    document_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='financial_report', null=True)
    valid_from = models.DateField(auto_now_add=True, blank=False)
    public = models.BooleanField(default=True)

    def belongs_to_host(self, host):
        return self.host == host

    class Meta:
        get_latest_by = 'published'

    def __str__(self):
        city = ("(" + self.host.city + ")") if self.host else ''
        return self.title + " " + city


class Team(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, null=False, blank=False)
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
        return "" # TODO

    @staticmethod
    def get_model_name():
        return "Team"

    def __str__(self):
        return self.name + " (" + self.host.name + ")"

    def validate_unique(self, *args, **kwargs):
        super(Team, self).validate_unique(*args, **kwargs)

        same_host_and_slug = Team.objects.filter(host=self.host, slug=self.slug)

        if same_host_and_slug.exists() and (self not in same_host_and_slug):  # second part is necessary to be able to edit a team. Otherwise saving after editing will raise slug already exists error
            print(same_host_and_slug, "\n", self)
            raise ValidationError(
                {
                    NON_FIELD_ERRORS: [
                        'The \"slug\" ' + self.slug + ' already exist!',
                    ],
                }
            )

    class Meta:
        ordering = ['rank', 'name']


class TeamUserRelation(models.Model):
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


class Donation(models.Model):
    host = models.ForeignKey(Host, on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    note = models.TextField(null=True, blank=True)

    def belongs_to_host(self, host):
        return self.host == host

    def __str__(self):
        project = ("(" + self.project.name + ")") if self.project else ''
        return str(self.amount) + "€ für " + self.host.city + project


class Milestone(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return "Milestone für " + self.project.name

    def belongs_to_host(self, host):
        return self.project.belongs_to_host(host)


class Milestep(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    milestone = models.ForeignKey(Milestone, on_delete = models.CASCADE)
    date = models.DateField(null=True, blank=True)
    reached = models.BooleanField()

    def belongs_to_host(self, host):
        return self.milestone.belongs_to_host(host)

    def __str__(self):
        return self.name + ' (' + self.milestone.project.name + ')'


class BankAccount(models.Model):
    account_holder = models.CharField(max_length=100)
    profile = models.OneToOneField(User, on_delete=models.CASCADE)
    iban = IBANField(include_countries=IBAN_SEPA_COUNTRIES)
    bic = BICField()

    def belongs_to_host(self, host):
        return self.profile.belongs_to_host(host)

    def __str__(self):
        return 'Bankdaten von '+self.profile.name()


class ContactMessage(models.Model):
    REASON_CHOICES = (
        ('spende', 'Spende'),
        ('austritt', 'Austritt'),
        ('other', 'Sonstiges')
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


