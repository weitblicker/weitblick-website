# see https://docs.djangoproject.com/en/2.2/ref/contrib/sitemaps/#django.contrib.sitemaps.views.sitemap

from django.contrib.sitemaps import Sitemap
from .models import NewsPost
from .models import Project
from .models import BlogPost
from .models import Event
from django.urls import reverse
from datetime import datetime


class NewsPostSitemap(Sitemap):
    def changefreq(self, obj):
        return "never"

    def priority(self, obj):
        return 0.5

    def items(self):
        return NewsPost.objects.filter()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return reverse('news-post', args=[obj.pk])


class ProjectSitemap(Sitemap):
    def changefreq(self, obj):
        return "never"

    def priority(self, obj):
        return 0.5

    def items(self):
        return Project.objects.filter()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return reverse('project', args=[obj.slug])


class BlogPostSitemap(Sitemap):
    def changefreq(self, obj):
        return "never"

    def priority(self, obj):
        return 0.5

    def items(self):
        return BlogPost.objects.filter()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return reverse('blog-post', args=[obj.pk])


class EventSitemap(Sitemap):
    def changefreq(self, obj):
        return "never"

    def priority(self, obj):
        return 0.5

    def items(self):
        return Event.objects.filter()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return reverse('event', args=[obj.event_slug])

