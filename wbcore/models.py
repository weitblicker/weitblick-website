from django.db import models
from django_countries.fields import CountryField
from django.contrib.auth.models import User
from photologue.models import Gallery
from os.path import splitext
from localflavor.generic.models import IBANField
from localflavor.generic.models import BICField
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES


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
    lng = models.DecimalField(max_digits=11, decimal_places=8)
    lat = models.DecimalField(max_digits=11, decimal_places=8)
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
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True)
    logo = models.ImageField(upload_to=save_host_logo)

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

    def host_name_list(self):
        host_names = [host.name for host in self.hosts.all()]
        return ", ".join(host_names)

    def __str__(self):
        return self.name


class CustomGallery(models.Model):
    gallery = models.OneToOneField(Gallery, related_name='extended',on_delete=models.CASCADE)
    project = models.ForeignKey(Project,on_delete=models.SET_NULL, null=True, blank =True)
    def __str__(self):
        return self.gallery.title


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
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    since = models.DateField(auto_now_add=True)
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
    host = models.ForeignKey(Host, to_field='slug', on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_str = models.CharField(max_length=200, null=True, blank=True)
    gallery = models.ForeignKey(Gallery, null=True, blank =True, on_delete=models.SET_NULL)

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
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    class Meta:
        get_latest_by = 'published'

    def __str__(self):
        city = ("(" + self.host.city + ")") if self.host else ''
        return self.title + " " + city


class Team(models.Model):
    name = models.CharField(max_length=100)
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
        project = ("(" + self.project.name + ")") if self.host else ''
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
    
    
    
    
    


