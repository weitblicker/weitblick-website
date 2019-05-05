# see https://docs.djangoproject.com/en/2.2/ref/contrib/sitemaps/#django.contrib.sitemaps.views.sitemap
# see https://www.sitemaps.org/protocol.html

from django.contrib.sitemaps import Sitemap
from .models import NewsPost
from .models import Project
from .models import BlogPost
from .models import Event
from .models import Team
from .models import Host
from django.urls import reverse
from django.utils.dateparse import parse_date
from datetime import datetime


class NewsPostSitemap(Sitemap):
    def changefreq(self, obj):
        return "never"

    def priority(self, obj):
        return 0.5

    def items(self):
        return NewsPost.objects.filter()

    def lastmod(self, obj):
        return obj.updated

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
        if obj.updated:
            return obj.datetime
        elif obj.published:
            return obj.published
        else:
            return parse_date('2008-01-01')

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
        return obj.updated

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


class TeamSitemap(Sitemap):
    def changefreq(self, obj):
        return "never"

    def priority(self, obj):
        return 0.5

    def items(self):
        return Team.objects.filter()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return reverse('team', args=[obj.host_slug])


class HostSitemap(Sitemap):
    def changefreq(self, obj):
        return "never"

    def priority(self, obj):
        return 0.5

    def items(self):
        return Host.objects.filter()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return reverse('host', args=[obj.slug])
