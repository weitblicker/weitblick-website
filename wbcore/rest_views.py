import json
import os
import uuid

from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Sum
from django.http import HttpResponse, Http404, JsonResponse
from django.template import loader
from martor.utils import LazyEncoder
from django.utils.translation import ugettext_lazy as _
from rest_auth.models import TokenModel
from rest_auth.views import UserDetailsView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from wbcore.serializers import (NewsPostSerializer, BlogPostSerializer, HostSerializer, EventSerializer,
                                ProjectSerializer, LocationSerializer, CycleDonationSerializer,
                                CycleDonationRelationSerializer, CycleSegmentSerializer, CycleTourSerializer,
                                TokenSerializer, UserCycleSerializer, FAQSerializer, UserSerializer, TeamSerializer)
from wbcore.models import (NewsPost, BlogPost, Host, Event, Project, Location, Photo, CycleDonation, CycleTour, User,
                           FAQ, Team)

from rest_framework import status, viewsets, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from allauth.account.views import ConfirmEmailView
from slugify import slugify

from weitblick import settings
from .filter import filter_events, filter_projects, filter_news, filter_blog

image_types = [
    'image/png', 'image/jpg',
    'image/jpeg', 'image/pjpeg', 'image/gif'
]

replacements = {
    ' ': '-',
    'ä': 'ae',
    'ö': 'oe',
    'ü': 'ue',
}


@login_required
def markdown_uploader(request):
    """
    Makdown image upload for locale storage
    and represent as json to markdown editor.
    """
    if request.method == 'POST' and request.is_ajax():
        if 'markdown-image-upload' in request.FILES:
            image = request.FILES['markdown-image-upload']
            if image.content_type not in image_types:
                data = json.dumps({
                    'status': 405,
                    'error': _('Bad image format.')
                }, cls=LazyEncoder)
                return HttpResponse(
                    data, content_type='application/json', status=405)

            if image.size > settings.MAX_IMAGE_UPLOAD_SIZE:
                to_MB = settings.MAX_IMAGE_UPLOAD_SIZE / (1024 * 1024)
                data = json.dumps({
                    'status': 405,
                    'error': _('Maximum image file is %(size) MB.') % {'size': to_MB}
                }, cls=LazyEncoder)
                return HttpResponse(
                    data, content_type='application/json', status=405)

            name = image.name.lower()
            for k, i in replacements.items():
                name = name.replace(k, i)

            img_uuid = "{0}-{1}".format(uuid.uuid4().hex[:10], name)
            tmp_file = os.path.join(settings.MARTOR_UPLOAD_PATH, img_uuid)
            def_path = default_storage.save(tmp_file, ContentFile(image.read()))
            img_url = os.path.join(settings.MEDIA_URL, def_path)

            data = json.dumps({
                'status': 200,
                'link': img_url,
                'name': name
            })
            return HttpResponse(data, content_type='application/json')
        return HttpResponse(_('Invalid request!'))
    return HttpResponse(_('Invalid request!'))


@api_view(['GET'])
def host_list(request, format=None):
    if request.method == 'GET':
        hosts = Host.objects.all()
        serializer = HostSerializer(hosts, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def host_detail(request, pk, format=None):
    try:
        host = Host.objects.get(pk=pk)
    except Host.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = HostSerializer(host)
        return Response(serializer.data)


@api_view(['GET'])
def event_list(request, format=None):
    if request.method == 'GET':
        occ, events = filter_events(request)
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def event_detail(request, pk, format=None):
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EventSerializer(event)
        return Response(serializer.data)


@api_view(['GET'])
def project_list(request, format=None):
    if request.method == 'GET':
        projects = filter_projects(request)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def project_detail(request, pk, format=None):
    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProjectSerializer(project, context={'request': request})
        return Response(serializer.data)


@api_view(['GET'])
def news_list(request, format=None):
    if request.method == 'GET':
        posts = filter_news(request)
        serializer = NewsPostSerializer(posts, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def news_detail(request, pk, format=None):
    try:
        post = NewsPost.objects.get(pk=pk)
    except NewsPost.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = NewsPostSerializer(post)
        return Response(serializer.data)


@api_view(['GET'])
def account_confirm_email(request, key):
    emailconfirmation = EmailConfirmationHMAC.from_key(key)
    if not emailconfirmation:
        queryset = EmailConfirmation.objects.all_valid()
        queryset = queryset.select_related("email_address__user")
        try:
            emailconfirmation = queryset.get(key=key.lower())
        except EmailConfirmation.DoesNotExist:
            raise Http404()

    emailconfirmation.confirm(request)
    return Response("Test")


@api_view(['GET'])
def blog_list(request, format=None):
    if request.method == 'GET':
        posts = filter_blog(request)
        serializer = BlogPostSerializer(posts, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def blog_detail(request, pk, format=None):
    try:
        post = BlogPost.objects.get(pk=pk)
    except BlogPost.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BlogPostSerializer(post)
        return Response(serializer.data)


@api_view(['GET'])
def location_list(request, format=None):
    if request.method == 'GET':
        locations = Location.objects.all()
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def location_detail(request, pk, format=None):
    try:
        location = Location.objects.get(pk=pk)
    except Location.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = LocationSerializer(location)
        return Response(serializer.data)


@api_view(['GET'])
def cycle_donations_list(request):
    if request.method == 'GET':
        cycle_donations = CycleDonation.objects.all()
        serializer = CycleDonationSerializer(cycle_donations, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def cycle_donation(request, pk):
    if request.method == 'GET':
        try:
            cycle_donation = CycleDonation.objects.get(pk=pk)
            serializer = CycleDonationSerializer(cycle_donation)
            return Response(serializer.data)
        except CycleDonation.DoesNotExist:
            return Response(status.HTTP_404_NOT_FOUND)


class CycleAddSegmentViewSet(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = CycleSegmentSerializer(request.user, data=request.data)
        if serializer.is_valid():
            segment = serializer.save()
            tour_serializer = CycleTourSerializer(segment.tour)
            return Response(tour_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CycleUserToursViewSet(viewsets.ModelViewSet):
    serializer_class = CycleTourSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.cycletour_set.all()


class CycleNewUserTourViewSet(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        max_index_tour = CycleTour.objects.filter(user=request.user).order_by('-index').first()
        tour_index = max_index_tour.index + 1 if max_index_tour else 0
        return Response(data={'tour_index': tour_index}, status=status.HTTP_201_CREATED)


def get_best_users():
    users = User.objects.annotate(
        euro=Sum('cycletour__euro'),
        km=Sum('cycletour__km')
    ).exclude(cycletour=None)

    return users


# TODO use user for getting the user field around the user's ranking
def get_user_field(user):
    users = User.objects.annotate(
        euro=Sum('cycletour__euro'),
        km=Sum('cycletour__km')
    ).exclude(cycletour=None)
    return users


class CycleRankingViewSet(APIView):

    serializer_class = UserCycleSerializer

    def get(self, request):
        if not request.user.is_anonymous:
            user_field = get_user_field(request.user)
            if 'ordering' in request.GET and request.GET['ordering'] == 'euro':
                user_field = user_field.order_by('-euro')
            else:
                user_field = user_field.order_by('-km')

            user_field = self.serializer_class(user_field, many=True).data
        else:
            user_field = None

        best_users = get_best_users()
        if 'ordering' in request.GET and request.GET['ordering'] == 'euro':
            best_users = best_users.order_by('-euro')
        else:
            best_users = best_users.order_by('-km')

        best_field = self.serializer_class(best_users, many=True).data

        return Response({
            'user_field': user_field,
            'best_field': best_field
        })


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer


class AGBView(APIView):

    def get(self, request):
        template = loader.get_template('wbcore/app_agb.html')
        text = template.render({}, request)
        image = static("images/agb_header.jpg")
        return JsonResponse({'title': "Allgemeine Geschäftsbedingungen", 'image': image, 'text': text}, status=status.HTTP_200_OK)


class ContactView(APIView):
    def get(self, request):
        template = loader.get_template('wbcore/app_contact.html')
        text = template.render({}, request)
        image = static("images/contact_header.jpg")
        return JsonResponse({'title': "Kontakt", 'image': image, 'text': text}, status=status.HTTP_200_OK)


class CreditsView(APIView):
    def get(self, request):
        try:
            team = Team.objects.get(slug="app-developers")
            serializer = TeamSerializer(instance=team)
            return Response(serializer.data)
        except Team.DoesNotExist:
            return Response("App Developers Team not available on Server")


class UsersView(RetrieveUpdateAPIView):
    """
    Reads and updates UserModel fields
    Accepts GET, PUT, PATCH methods.

    Default accepted fields: username, first_name, last_name
    Default display fields: pk, username, email, first_name, last_name
    Read-only fields: pk, email

    Returns UserModel fields.
    """
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, )

    def post(self, request, format=None):

        serializer = self.serializer_class(
            instance=request.user,
            data=request.data,
            context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)

        return JsonResponse(serializer.errors, status=400)

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        """
        Adding this method since it is sometimes called when using
        django-rest-swagger
        https://github.com/Tivix/django-rest-auth/issues/275
        """
        return get_user_model().objects.none()


