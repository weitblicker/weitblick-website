from abc import ABC

import datetime
from django.utils import timezone
from rest_auth.serializers import UserDetailsSerializer
from schedule.models import Occurrence

from wbcore.cycle_statistics import get_cycle_stats
from wbcore.models import (
    NewsPost, BlogPost, Host, Event, Project, Location, CycleDonation, CycleDonationRelation, CycleSegment,
    CycleTour, User, FAQ, QuestionAndAnswer, Partner, Address, BankAccount, Milestone)
from rest_framework import serializers
from photologue.models import Gallery, Photo
from rest_auth.models import TokenModel
from django.db.models import Sum


def get_author(post):
    author_image = None
    if post.author:
        if post.author.image:
            author_image = post.author.image.url
        author_name = post.author.name()
    else:
        author_name = post.author_str

    return {
        'name': author_name,
        'image': author_image
    }


class PhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, photo):
        if photo:
            return photo.get_rest_url()

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
        fields = ('id', 'name', 'description', 'country', 'postal_code', 'city', 'state', 'street', 'address',
                  'lat', 'lng', 'map_zoom')


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


class BlogPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    image = PhotoSerializer(source='get_title_image')
    photos = PhotoSerializer(many=True)
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")
    author = serializers.SerializerMethodField()
    host = HostSerializer()
    location = LocationSerializer()

    def get_author(self, post):
        return get_author(post)

    class Meta:
        model = BlogPost
        fields = ('id', 'title', 'text', 'image', 'published', 'range', 'teaser', 'photos', 'project', 'author', 'host',
                  'location')


class NewsPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    photos = PhotoSerializer(many=True)
    image = PhotoSerializer(source='get_title_image')
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")
    author = serializers.SerializerMethodField()
    host = HostSerializer()

    def get_author(self, post):
        return get_author(post)

    class Meta:
        model = NewsPost
        fields = ('id', 'title', 'text', 'image', 'published', 'range', 'teaser', 'photos', 'project', 'host', 'author')


class CycleDonationRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CycleDonationRelation
        fields = ('project', 'cycle_donation', 'current_amount', 'goal_amount', 'finished')


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ('name', 'description', 'date', 'reached')


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


class CycleDonationSponsorSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    partner = PartnerSerializer()

    class Meta:
        model = CycleDonation
        fields = ('id', 'partner', 'name', 'description', 'goal_amount', 'rate_euro_km',)


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    photos = PhotoSerializer(many=True)
    image = PhotoSerializer(source='get_title_image')
    #cycle = CycleDonationRelationSerializer(many=True, source='cycledonationrelation_set')
    cycle = serializers.SerializerMethodField()
    location = LocationSerializer()
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%z")
    partners = PartnerSerializer(many=True)
    hosts = HostSerializer(many=True)
    milestones = MilestoneSerializer(many=True)
    donation_account = BankAccountSerializer()

    def get_cycle(self, project):
        stats = get_cycle_stats(project)
        cycle_donations = project.cycledonation_set.all()

        if stats and cycle_donations:
            print(stats)

            donation_goal_sum = 0
            for cycle_don_rel in project.cycledonationrelation_set.all():
                donation_goal_sum += cycle_don_rel.goal_amount if cycle_don_rel.goal_amount else cycle_don_rel.cycle_donation.goal_amount

            euro_sum = stats['euro_sum'] or 0
            km_sum = stats['km_sum'] or 0
            cyclists = stats['cyclists'] or 0
            progress = euro_sum / donation_goal_sum if donation_goal_sum else 0

            return {
                'km_sum': km_sum,
                'euro_sum': euro_sum,
                'cyclists': cyclists,
                'euro_goal': donation_goal_sum,
                'progress': progress,
                'donations': CycleDonationSponsorSerializer(instance=cycle_donations, many=True).data,
            }
        return None

    class Meta:
        model = Project

        depth = 0
        fields = ('id', 'start_date', 'end_date', 'image', 'published', 'name', 'slug', 'hosts', 'description',
                  'location', 'partners', 'photos', 'cycle', 'news', 'blog', 'donation_goal', 'goal_description',
                  'donation_current', 'milestones', 'events', 'cycle', 'donation_account')


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


class CycleProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    cycle = serializers.SerializerMethodField()
    hosts = HostSerializer(many=True)

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
