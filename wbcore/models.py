from django.db import models
from django_countries.fields import CountryField
from django.contrib.auth.models import User
from os.path import splitext


class Address(models.Model):
    name = models.CharField(max_length=200)
    country = CountryField()
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=30)
    state = models.CharField(max_length=30)
    street = models.CharField(max_length=30)

    def __str__(self):
        return ", ".join(filter(None, [self.name, self.street, self.postal_code, self.city, self.country.name]))


class Location(models.Model):
    name = models.CharField(max_length=200, unique=True)
    lng = models.DecimalField(max_digits=8, decimal_places=3)
    lat = models.DecimalField(max_digits=8, decimal_places=3)
    description = models.TextField(blank=True, null=True)
    country = CountryField()
    postal_code = models.CharField(blank=True, null=True, max_length=20)
    city = models.CharField(blank=True, null=True, max_length=30)
    state = models.CharField(blank=True, null=True, max_length=30)
    street = models.CharField(blank=True, null=True, max_length=30)

    def __str__(self):
        return self.name + " (" + self.country.name + ")"


def save_host_logo(instance, filename):
    return "hosts/" + instance.slug.lower() + splitext(filename)[1].lower()


class Host(models.Model):
    slug = models.SlugField(primary_key=True, max_length=50, unique=True)
    name = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    founding_date = models.DateField()
    address = models.OneToOneField(Address, on_delete=models.CASCADE)
    logo = models.ImageField(upload_to=save_host_logo)

    def __str__(self):
        return self.name


def save_partner_logo(instance, filename):
    return "partners/" + instance.name.lower().replace(' ', '_') + path.splittext(filename)[1].lower()


class Partner(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    logo = models.ImageField(upload_to=save_partner_logo)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True, null=True)
    hosts = models.ManyToManyField(Host)
    short_description = models.TextField()
    description = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True)

    def host_name_list(self):
        host_names = [host.name for host in self.hosts.all()]
        return ", ".join(host_names)

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=200)
    projects = models.ManyToManyField(Project, null=True, blank=True)
    host = models.ForeignKey(Host, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    host = models.ManyToManyField(Host, blank=True, )
    image = models.ImageField(null=True, blank=True)


class Post(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    image = models.ImageField(null=True, blank=True, upload_to="posts")
    img_alt = models.CharField(max_length=300)
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
    host = models.ForeignKey(Host, to_field='slug', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_str = models.CharField(max_length=200, null=True, blank=True)

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
# Create your models here.

