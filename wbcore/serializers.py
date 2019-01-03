from wbcore.models import NewsPost, BlogPost, Host, Event, Project
from rest_framework import serializers


class BlogPostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BlogPost
        fields = ('title', 'text', 'image', 'added', 'updated', 'published', 'range', 'teaser')


class NewsPostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NewsPost
        fields = ('title', 'text', 'image', 'added', 'updated', 'published', 'range', 'teaser')


class HostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Host
        fields = ('name', 'slug', 'city')


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = ('name', 'slug', 'hosts', 'description', 'location', 'partner')


class EventSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Event
        fields = ('name', 'projects', 'host')
