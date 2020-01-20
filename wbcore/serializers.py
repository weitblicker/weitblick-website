from abc import ABC

from allauth.account.forms import default_token_generator
from rest_auth.serializers import UserDetailsSerializer, UserModel
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from wbcore.models import (
    NewsPost, BlogPost, Host, Event, Project, Location, CycleDonation, CycleDonationRelation, CycleSegment,
    CycleTour, User, FAQ, QuestionAndAnswer)
from rest_framework import serializers
from photologue.models import Gallery, Photo
from django.utils.dateparse import parse_datetime
from rest_auth.models import TokenModel
from django.db.models import Sum

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


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')

    class Meta:
        model = Location
        fields = ('id', 'name', 'description', 'country', 'postal_code', 'city', 'state', 'street', 'address', 'lat', 'lng')


class BlogPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    gallery = GallerySerializer(read_only=True)
    image = PhotoSerializer()
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")

    class Meta:
        model = BlogPost
        fields = ('id', 'title', 'text', 'image', 'published', 'range', 'teaser', 'gallery')


class NewsPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    photos = PhotoSerializer(many=True)
    image = PhotoSerializer(source='get_title_image')
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")

    class Meta:
        model = NewsPost
        fields = ('id', 'title', 'text', 'image', 'published', 'range', 'teaser', 'photos')


class HostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')
    class Meta:
        model = Host
        fields = ('id', 'name', 'city')


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    photos = PhotoSerializer(many=True)
    image = PhotoSerializer(source='get_title_image')
    cycle = serializers.SerializerMethodField()
    location = LocationSerializer()
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")

    def get_cycle(self, project):
        qs = project.cycledonationrelation_set.all()
        serializer = CycleDonationRelationSerializer(many=True, instance=qs)
        return serializer.data

    class Meta:
        model = Project

        depth = 0
        fields = ('id', 'start_date', 'end_date', 'image', 'published', 'name', 'slug', 'hosts', 'description',
                  'location', 'partners', 'photos', 'cycle', 'news', 'blog')


class EventSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    gallery = GallerySerializer(read_only=True)

    class Meta:
        model = Event
        fields = ('id', 'name', 'projects', 'host', 'gallery')


class CycleDonationRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CycleDonationRelation
        fields = ('project', 'cycle_donation', 'current_amount', 'goal_amount', 'finished')


class CycleSegmentSerializer(serializers.ModelSerializer):
    token = serializers.CharField(write_only=True)
    project = serializers.IntegerField(write_only=True)
    tour = serializers.IntegerField(write_only=True)

    class Meta:
        model = CycleSegment
        fields = ('start', 'end', 'distance', 'project', 'tour', 'token')

    def create(self, validated_data):
        user = validated_data['user']
        tour_index = validated_data['tour']
        project = validated_data['project']

        try:
            tour = CycleTour.objects.get(user=user, index=tour_index)

        except CycleTour.DoesNotExist:
            # start new tour and finish all unfinished tours for the given user
            unfinished_tours = CycleTour.objects.filter(user=user, finished=False).all()
            for tour in unfinished_tours:
                tour.finished = True
                tour.save()

            # create new tour
            tour = CycleTour(user=user, index=tour_index, project=project)
            tour.save()

        tour.donations.set(project.cycledonation_set.all())
        tour.save()
        print("Tour donations:", tour.donations.all())

        segment = CycleSegment(start=validated_data['start'], end=validated_data['end'],
                               distance=validated_data['distance'], tour=tour)
        segment.save()
        return segment

    def validate(self, data):
        try:
            token = TokenModel.objects.get(key=data['token'])
            data['user'] = token.user
        except TokenModel.DoesNotExist:
            print("Token %s is invalid!" % data['token'])
            raise serializers.ValidationError("Token is invalid:%s" % data['token'])

        try:
            project = Project.objects.get(pk=data['project'])
            data['project'] = project
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project with the id %s does not exist!" % data['project'])

        if data['tour'] < 0:
            raise serializers.ValidationError("Tour index is negative!")

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


class CycleProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    cycle = serializers.SerializerMethodField()

    def get_cycle(self, project):
        qs = project.cycledonationrelation_set.all()
        serializer = CycleDonationRelationSerializer(many=True, instance=qs)
        return serializer.data

    class Meta:
        model = Project

        depth = 0
        fields = ('id', 'hosts', 'cycle')


class TokenSerializer(serializers.ModelSerializer):
    token = serializers.CharField(write_only=True)

    class Meta:
        model = TokenModel
        fields = ('token',)

    def validate(self, data):
        print(data)
        try:
            self.instance = TokenModel.objects.get(key=data['token'])
        except TokenModel.DoesNotExist:
            print("Token %s is invalid!" % data['token'])
            raise serializers.ValidationError("Token is invalid:%s" % data['token'])

        return data


class CycleTourSerializer(serializers.ModelSerializer):
    tour = serializers.IntegerField(source='index')
    project = serializers.SerializerMethodField()

    def get_project(self, tour):
        serializer = CycleProjectSerializer(read_only=True, instance=tour.project)
        return serializer.data

    def validate(self, data):
        try:
            token = TokenModel.objects.get(key=data['token'])
            data['user'] = token.user
        except TokenModel.DoesNotExist:
            print("Token %s is invalid!" % data['token'])
            raise serializers.ValidationError("Token is invalid:%s" % data['token'])

        return data

    class Meta:
        model = CycleTour
        fields = ('tour', 'project', 'finished', 'euro', 'km', 'start', 'end', 'duration')


class UserSerializer(UserDetailsSerializer):
    """
    User model w/o password
    """
    class Meta:
        model = User
        fields = ('pk', 'username', 'email', 'first_name', 'last_name', 'image')
        read_only_fields = ('email', )


class UserCycleSerializer(serializers.ModelSerializer):

    km = serializers.FloatField()
    euro = serializers.FloatField()

    def get_queryset(self):
        return self.queryset.annotate(
            euro=Sum('cycletour__euro'),
            km=Sum('cycletour__km')
        )

    def get_km(self, user):
        user_tours = CycleTour.objects.filter(user=user)
        return user_tours.aggregate(Sum('km'))

    def get_euro(self, user):
        user_tours = CycleTour.objects.filter(user=user)
        return user_tours.aggregate(Sum('euro'))

    class Meta:
        model = User
        fields = ('username', 'image', 'km', 'euro')


class QuestionAndAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAndAnswer
        fields = ('question', 'answer',)


class FAQSerializer(serializers.ModelSerializer):
    faqs = serializers.SerializerMethodField()

    def get_faqs(self, faq):
        return QuestionAndAnswerSerializer(many=True, instance=faq.questionandanswer_set.all()).data

    class Meta:
        model = FAQ
        fields = ('title', 'faqs',)
