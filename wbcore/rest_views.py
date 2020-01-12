import json
import os
import uuid

from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Sum
from django.http import HttpResponse, Http404, JsonResponse
from martor.utils import LazyEncoder
from django.utils.translation import ugettext_lazy as _
from rest_auth.models import TokenModel
from rest_auth.views import UserDetailsView
from rest_framework.parsers import MultiPartParser

from wbcore.serializers import (NewsPostSerializer, BlogPostSerializer, HostSerializer, EventSerializer,
                                ProjectSerializer, LocationSerializer, CycleDonationSerializer,
                                CycleDonationRelationSerializer, CycleSegmentSerializer, CycleTourSerializer,
                                TokenSerializer, UserCycleSerializer, FAQSerializer, UserSerializer)
from wbcore.models import NewsPost, BlogPost, Host, Event, Project, Location, Photo, CycleDonation, CycleTour, User, FAQ
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
        print(request.POST, request.path)
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
        events = filter_events(request)
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

    print("confirmation:", emailconfirmation.confirm(request), emailconfirmation.email_address.verified)

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


@api_view(['POST'])
def cycle_add_segment(request):
    if request.method == 'POST':
        serializer = CycleSegmentSerializer(data=request.data)
        if serializer.is_valid():
            segment = serializer.save()
            tour_serializer = CycleTourSerializer(segment.tour)
            return Response(tour_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def cycle_user_tours(request):
    if request.method == 'POST':
        try:
            token_serializer = TokenSerializer(data=request.data)
            if token_serializer.is_valid():
                token = token_serializer.instance
                serializer = CycleTourSerializer(instance=token.user.cycletour_set.all(), many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(token_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TokenModel.DoesNotExist:
            print("Token %s does not exist!" % token_str)
            return Response(status=status.HTTP_400_BAD_REQUEST)


def get_best_users():
    users = User.objects.annotate(
        euro=Sum('cycletour__euro'),
        km=Sum('cycletour__km')
    ).exclude(cycletour=None)

    return users


def get_user_field(user):
    users = User.objects.annotate(
        euro=Sum('cycletour__euro'),
        km=Sum('cycletour__km')
    ).exclude(cycletour=None)
    return users


@api_view(['GET', 'POST'])
def cycle_ranking(request):

    best_users = get_best_users()
    if 'ordering' in request.GET and request.GET['ordering'] == 'euro':
        best_users = best_users.order_by('-euro')
    else:
        best_users = best_users.order_by('-km')

    token_serializer = TokenSerializer(data=request.data, many=False)

    if token_serializer.is_valid():
        user = token_serializer.instance.user
        user_field = get_user_field(user)
        if 'ordering' in request.GET and request.GET['ordering'] == 'euro':
            user_field = user_field.order_by('-euro')
        else:
            user_field = user_field.order_by('-km')

        user_field = UserCycleSerializer(user_field, many=True).data

    else:
        user_field = None

    best_field = UserCycleSerializer(best_users, many=True).data

    return Response({
            'user_field': user_field,
            'best_field': best_field
        })


class RankingViewSet(viewsets.ModelViewSet):
    queryset = User.objects.exclude(cycletour=None)
    serializer_class = UserCycleSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['km', 'euro']
    ordering = ['km']

    def get_queryset(self):
        return self.queryset.annotate(
            euro=Sum('cycletour__euro'),
            km=Sum('cycletour__km')
        )


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer


class UserrankingViewSet(object):
    queryset = User.objects.exclude(cycletour=None)
    serializer_class = UserCycleSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['km', 'euro']
    ordering = ['km']

    def get_queryset(self):
        return self.queryset.annotate(
            euro=Sum('cycletour__euro'),
            km=Sum('cycletour__km')
        )


class UsersView(UserDetailsView):
    """
    Reads and updates UserModel fields
    Accepts GET, PUT, PATCH methods.

    Default accepted fields: username, first_name, last_name
    Default display fields: pk, username, email, first_name, last_name
    Read-only fields: pk, email

    Returns UserModel fields.
    """
    parser_classes = (MultiPartParser, )

    def post(self, request, format=None):
        print(request.FILES)
        serializer = UserSerializer(data=request.data)
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


