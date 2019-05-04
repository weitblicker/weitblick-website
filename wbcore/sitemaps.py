from django.contrib.sitemaps import Sitemap
from .models import NewsPost
from .models import Project
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
        return 'hello'


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
        return 'hi'

