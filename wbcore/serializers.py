from abc import ABC

import datetime
from django.utils import timezone
from rest_auth.serializers import UserDetailsSerializer
from schedule.models import Occurrence

from wbcore.models import (
    NewsPost, BlogPost, Host, Event, Project, Location, CycleDonation, CycleDonationRelation, CycleSegment,
    CycleTour, User, FAQ, QuestionAndAnswer, Partner, Address, BankAccount)
from rest_framework import serializers
from photologue.models import Gallery, Photo
from rest_auth.models import TokenModel
from django.db.models import Sum


class PhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, photo):
        if photo:
            return photo.get_listsize_url()

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


class AddressSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    def get_country(self, address):
        return address.country.name

    class Meta:
        model = Address
        fields = ('name', 'country', 'postal_code', 'city', 'state', 'street')


class PartnerSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = Partner
        fields = ('name', 'description', 'address', 'logo', 'link')


class BlogPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    image = PhotoSerializer(source='get_title_image')
    photos = PhotoSerializer(many=True)
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")

    class Meta:
        model = BlogPost
        fields = ('id', 'title', 'text', 'image', 'published', 'range', 'teaser', 'photos', 'project')


class NewsPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    photos = PhotoSerializer(many=True)
    image = PhotoSerializer(source='get_title_image')
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")

    class Meta:
        model = NewsPost
        fields = ('id', 'title', 'text', 'image', 'published', 'range', 'teaser', 'photos', 'project')


class BankAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccount
        fields = ('account_holder', 'iban', 'bic')


class HostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')
    address = AddressSerializer()
    location = LocationSerializer()
    bank_account = BankAccountSerializer(source='bank')

    class Meta:
        model = Host
        fields = ('id', 'name', 'city', 'founding_date', 'address', 'location', 'partners', 'bank_account')


class CycleDonationRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CycleDonationRelation
        fields = ('project', 'cycle_donation', 'current_amount', 'goal_amount', 'finished')


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    photos = PhotoSerializer(many=True)
    image = PhotoSerializer(source='get_title_image')
    cycle = CycleDonationRelationSerializer(many=True, source='cycledonationrelation_set')
    location = LocationSerializer()
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")
    partners = PartnerSerializer(many=True)

    class Meta:
        model = Project

        depth = 0
        fields = ('id', 'start_date', 'end_date', 'image', 'published', 'name', 'slug', 'hosts', 'description',
                  'location', 'partners', 'photos', 'cycle', 'news', 'blog', 'donation_goal', 'goal_description',
                  'donation_current')


class OccurrenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occurrence
        fields = ('title', 'description', 'start', 'end', 'cancelled', 'original_start', 'original_end', 'updated_on')


class EventSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    gallery = GallerySerializer(read_only=True)
    host = HostSerializer()
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")
    photos = PhotoSerializer(many=True)
    image = PhotoSerializer(source='get_title_image')
    location = LocationSerializer()
    occurrences = serializers.SerializerMethodField()

    def get_occurrences(self, event):
        start = timezone.now()-datetime.timedelta(days=1)
        end = start + datetime.timedelta(days=365)
        return OccurrenceSerializer(instance=event.get_occurrences(start, end), many=True).data

    class Meta:
        model = Event
        fields = ('id', 'title', 'projects', 'gallery', 'host', 'published', 'location', 'image', 'photos', 'form',
                  'cost', 'start', 'end', 'description', 'rule', 'end_recurring_period', 'occurrences')


class CycleSegmentSerializer(serializers.ModelSerializer):
    project = serializers.IntegerField(write_only=True)
    tour = serializers.IntegerField(write_only=True)

    def __init__(self, user, **kwargs):
        self.user = user
        super().__init__(**kwargs)

    class Meta:
        model = CycleSegment
        fields = ('start', 'end', 'distance', 'project', 'tour',)

    def create(self, validated_data):
        tour_index = validated_data['tour']
        project = validated_data['project']

        try:
            tour = CycleTour.objects.get(user=self.user, index=tour_index)

        except CycleTour.DoesNotExist:
            # start new tour and finish all unfinished tours for the given user
            unfinished_tours = CycleTour.objects.filter(user=self.user, finished=False).all()
            for tour in unfinished_tours:
                tour.finished = True
                tour.save()

            # create new tour
            tour = CycleTour(user=self.user, index=tour_index, project=project)
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
    partner = PartnerSerializer()

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

    class Meta:
        model = CycleTour
        fields = ('tour', 'project', 'finished', 'euro', 'km', 'start', 'end', 'duration')


class UserSerializer(serializers.ModelSerializer):
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
        read_only_fields = ('question', 'answer')


class FAQSerializer(serializers.ModelSerializer):
    faqs = serializers.SerializerMethodField()

    def get_faqs(self, faq):
        return QuestionAndAnswerSerializer(many=True, instance=faq.questionandanswer_set.all()).data

    class Meta:
        model = FAQ
        fields = ('title', 'faqs',)
        read_only_fields = ('title', 'faqs')
