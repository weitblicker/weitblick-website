import datetime
from haystack import indexes
from wbcore.models import Host, NewsPost, Project, Event, BlogPost, Partner


class HostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    model = indexes.CharField(model_attr='get_model_name', faceted=True)

    def get_model(self):
        return Host

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class ProjectIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    model = indexes.CharField(model_attr='get_model_name', faceted=True)
    hosts_slug = indexes.MultiValueField()
    start_date = indexes.DateField(model_attr='start_date', null=True)
    end_date = indexes.DateField(model_attr='end_date', null=True)
    country_code = indexes.CharField()
    completed = indexes.BooleanField(model_attr='completed')

    def get_model(self):
        return Project

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_country_code(self, project):
        return project.location.country.code

    def prepare_hosts_slug(self, project):
        return [host.slug for host in project.hosts.all()]


class NewsPostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    model = indexes.CharField(model_attr='get_model_name', faceted=True)
    host_slug = indexes.CharField()
    published = indexes.DateTimeField(model_attr='published')

    def get_model(self):
        return NewsPost

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_host_slug(self, news_post):
        return news_post.host.slug if news_post.host else None


class BlogPostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    model = indexes.CharField(model_attr='get_model_name', faceted=True)
    host_slug = indexes.CharField()
    published = indexes.DateTimeField(model_attr='published')

    def get_model(self):
        return BlogPost

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_host_slug(self, blog_post):
        return blog_post.host.slug if blog_post.host else None



class EventsIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    model = indexes.CharField(model_attr='get_model_name', faceted=True)
    hosts_slug = indexes.MultiValueField()
    start = indexes.DateTimeField(model_attr='start')

    def get_model(self):
        return Event

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_hosts_slug(self, event):
        return [event.host.slug]


class PartnerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    model = indexes.CharField(model_attr='get_model_name', faceted=True)
    hosts_slug = indexes.MultiValueField()
    active = indexes.BooleanField(model_attr='active')
    category = indexes.CharField(model_attr='category')

    def get_model(self):
        return Partner

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_hosts_slug(self, partner):
        return [host.slug for host in Host.objects.all() if partner.belongs_to_host(host)]
