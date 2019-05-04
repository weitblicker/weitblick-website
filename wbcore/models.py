from django.db import models
from django_countries.fields import CountryField
from django.contrib.auth.models import User
from photologue.models import Gallery, Photo
from os.path import splitext
from localflavor.generic.models import IBANField
from localflavor.generic.models import BICField
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from django.urls import reverse
from django.conf import settings
from django_google_maps import fields as map_fields


class Address(models.Model):
    name = models.CharField(max_length=200)
    country = CountryField()
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=30)
    state = models.CharField(max_length=30, null=True, blank=True)
    street = models.CharField(max_length=30)

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
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True)

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


def save_partner_logo(instance, filename):
    return "partners/" + instance.name.lower().replace(' ', '_') + splitext(filename)[1].lower()


class Partner(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, blank=True, null=True)
    logo = models.ImageField(upload_to=save_partner_logo, null=True, blank=True)


    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True, null=True)
    hosts = models.ManyToManyField(Host)
    short_description = models.TextField()
    description = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)
    donation_goal = models.DecimalField(max_digits=11, decimal_places=2, null=True, blank=True)
    donation_current = models.DecimalField(max_digits=11, decimal_places=2, null=True, blank=True)
    gallery = models.ForeignKey(Gallery, blank=True, null=True, on_delete=models.SET_NULL)
    completed = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def host_name_list(self):
        host_names = [host.name for host in self.hosts.all()]
        return ", ".join(host_names)

    def __str__(self):
        return self.name

    def teaser_image(self):
        if self.gallery:
            return self.gallery.photos.first()
        else:
            return None


class Event(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True, null=True)
    projects = models.ManyToManyField(Project, blank=True)
    host = models.ManyToManyField(Host)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    gallery = models.ForeignKey(Gallery, null=True, blank =True,on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class Profile(models.Model):
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    host = models.ManyToManyField(Host, through='UserRelation')
    image = models.ImageField(null=True, blank=True)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True, blank=True)
    since = models.DateField(auto_now_add=True)
    until = models.DateField(null=True, blank=True)
    STATUS_CHOICES = (
        ('activ', 'Active'),
        ('left', 'Left')
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.name


class UserRelation(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    TYPE_CHOICES = (
        ('user', 'User'),
        ('member', 'Member'),
        ('pending', 'Pending')
    )
    member_type=models.CharField(max_length=20, choices=TYPE_CHOICES, default='pending')
    membership_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.profile.name + ' in ' + self.host.name


class NewsPost(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    image = models.ForeignKey(Photo, null=True, blank =True, on_delete=models.SET_NULL)
    added = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)
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

    def search_title(self):
        return self.title_de

    def search_url(self):
        return reverse('blog-post', args=[self.pk])

    def search_image(self):
        return self.image.get_search_mini_url() if self.image else ""

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
    valid_from = models.DateField(null=True, blank=True)

    class Meta:
        get_latest_by = 'published'

    def __str__(self):
        city = ("(" + self.host.city + ")") if self.host else ''
        return self.title + " " + city


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    host = models.ForeignKey(Host, on_delete=models.CASCADE, null=True)
    member = models.ManyToManyField(Profile)

    def __str__(self):
        city = ("(" + self.host.city + ")") if self.host else ''
        return self.name + " " + city


class Donation(models.Model):
    host = models.ForeignKey(Host, on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        project = ("(" + self.project.name + ")") if self.project else ''
        return str(self.amount) + "€ für " + self.host.city + project


class Milestone(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return "Milestone für " + self.project.name


class Milestep(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    milestone = models.ForeignKey(Milestone, on_delete = models.CASCADE)
    date = models.DateField(null=True, blank=True)
    reached = models.BooleanField()

    def __str__(self):
        return self.name + ' (' + self.milestone.project.name + ')'


class BankAccount(models.Model):
    account_holder = models.CharField(max_length=100)
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    iban = IBANField(include_countries=IBAN_SEPA_COUNTRIES)
    bic = BICField()

    def __str__(self):
        return 'Bankdaten von '+self.profile.name
