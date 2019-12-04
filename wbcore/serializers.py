from allauth.account.forms import default_token_generator
from rest_framework.exceptions import ValidationError

from wbcore.models import (
    NewsPost, BlogPost, Host, Event, Project, Location, CycleDonation, CycleDonationRelation, Segment, User)
from rest_framework import serializers
from photologue.models import Gallery, Photo
from django.utils.dateparse import parse_datetime
from rest_auth.models import TokenModel

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
    cycle = serializers.SerializerMethodField()

    def get_cycle(self, project):
        qs = project.cycledonationrelation_set.all()
        serializer = CycleDonationRelationSerializer(many=True, instance=qs)
        return serializer.data

    class Meta:
        model = Project

        depth = 0
        fields = ('id', 'start_date', 'end_date', 'published', 'name', 'slug', 'hosts', 'description', 'location',
                  'partners', 'gallery', 'cycle')


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


class CycleDonationRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CycleDonationRelation
        fields = ('project', 'cycle_donation', 'current_amount', 'goal_amount', 'finished')


class SegmentSerializer(serializers.ModelSerializer):
    token = serializers.CharField(write_only=True)

    class Meta:
        model = Segment
        fields = ('start', 'end', 'distance', 'project', 'tour', 'token')

    def create(self, validated_data):
        return Segment(start=validated_data['start'], end=validated_data['end'],
                       distance=validated_data['distance'], project=validated_data['project'],
                       tour=validated_data['tour'], user=validated_data['user'])

    def validate(self, data):
        try:
            print("validate...", data)
            token = TokenModel.objects.get(key=data['token'])
            print("Token:", token)
            data['user'] = token.user.pk
        except TokenModel.DoesNotExist:
            print("Token does not exist!")
            # raise serializers.ValidationError("Token is invalid:%s" % data['token'])
            data['user'] = User.objects.get(email="spuetz@uos.de")

        return data


class CycleDonationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    projects = serializers.SerializerMethodField()

    def get_projects(self, donation):
        qs = donation.cycledonationrelation_set.all()
        serializer = CycleDonationRelationSerializer(read_only=True, many=True, instance=qs)
        return serializer.data

    class Meta:
        model = CycleDonation
        fields = ('id', 'projects', 'partner', 'logo', 'name', 'description', 'goal_amount', 'rate_euro_km',)


class CycleSegmentSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')

    projects = serializers.SerializerMethodField()

    def get_projects(self, donation):
        qs = donation.cycledonationrelation_set.all()
        serializer = CycleDonationRelationSerializer(read_only=True, many=True, instance=qs)
        return serializer.data

    class Meta:
        model = CycleDonation
        fields = ('id', 'projects', 'partner', 'logo', 'name', 'description', 'goal_amount', 'rate_euro_km',)

