from wbcore.models import NewsPost, BlogPost, Host, Event, Project, Location
from rest_framework import serializers


class BlogPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    class Meta:
        model = BlogPost
        fields = ('id', 'title', 'text', 'image', 'added', 'updated', 'published', 'range', 'teaser')


class NewsPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    class Meta:
        model = NewsPost
        fields = ('id', 'title', 'text', 'image', 'added', 'updated', 'published', 'range', 'teaser')


class HostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')
    class Meta:
        model = Host
        fields = ('id', 'name', 'city')


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    class Meta:
        model = Project
        fields = ('id', 'name', 'slug', 'hosts', 'description', 'location', 'partner')


class EventSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    class Meta:
        model = Event
        fields = ('id', 'name', 'projects', 'host')


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    class Meta:
        model = Location
        fields = ('id', 'name', 'description', 'country', 'postal_code', 'city', 'state', 'street', 'address', 'lat', 'lng')
