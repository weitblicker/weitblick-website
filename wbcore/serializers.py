from wbcore.models import NewsPost, BlogPost, Host, Event, Project, Location
from rest_framework import serializers
from photologue.models import Gallery, Photo


class PhotoSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source='image')

    class Meta:
        model = Photo
        fields = ('id', 'title', 'caption', 'url', 'date_taken', 'crop_from')


class GallerySerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    def get_images(self, gallery):
        qs = gallery.photos.filter(is_public=True)
        serializer = PhotoSerializer(instance=qs, many=True)
        return serializer.data

    class Meta:
        model = Gallery
        depth = 1
        fields = ('id', 'title', 'description', 'images')


class BlogPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    gallery = GallerySerializer(read_only=True)
    image = PhotoSerializer()

    class Meta:
        model = BlogPost
        fields = ('id', 'title', 'text', 'image', 'added', 'updated', 'published', 'range', 'teaser', 'gallery')


class NewsPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    gallery = GallerySerializer(read_only=True)
    image = PhotoSerializer()

    class Meta:
        model = NewsPost
        fields = ('id', 'title', 'text', 'image', 'added', 'updated', 'published', 'range', 'teaser', 'gallery')


class HostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')
    class Meta:
        model = Host
        fields = ('id', 'name', 'city')


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    gallery = GallerySerializer(read_only=True)

    class Meta:
        model = Project
        depth = 0
        fields = ('id', 'start_date', 'end_date', 'published', 'name', 'slug', 'hosts', 'description', 'location',
                  'partner', 'gallery')


class EventSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    gallery = GallerySerializer(read_only=True)

    class Meta:
        model = Event
        fields = ('id', 'name', 'projects', 'host', 'gallery')


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')

    class Meta:
        model = Location
        fields = ('id', 'name', 'description', 'country', 'postal_code', 'city', 'state', 'street', 'address', 'lat', 'lng')
