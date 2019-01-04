import datetime
from haystack import indexes
from wbcore.models import Host, NewsPost, Project, Event, BlogPost


class HostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    model = indexes.CharField(model_attr='get_model_name', faceted=True)

    def get_model(self):
        return Host

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class NewsPostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    model = indexes.CharField(model_attr='get_model_name', faceted=True)

    def get_model(self):
        return NewsPost

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class BlogPostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    model = indexes.CharField(model_attr='get_model_name', faceted=True)

    def get_model(self):
        return BlogPost

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
