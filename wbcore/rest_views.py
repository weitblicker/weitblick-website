import json
import os
import uuid

from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse, Http404
from martor.utils import LazyEncoder
from django.utils.translation import ugettext_lazy as _

from wbcore.serializers import (NewsPostSerializer, BlogPostSerializer, HostSerializer, EventSerializer,
                                ProjectSerializer, LocationSerializer, CycleDonationSerializer,
                                CycleDonationRelationSerializer, SegmentSerializer)
from wbcore.models import NewsPost, BlogPost, Host, Event, Project, Location, Photo, CycleDonation
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from allauth.account.views import ConfirmEmailView

from weitblick import settings
from .filter import filter_events, filter_projects, filter_news, filter_blog


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
            image_types = [
                'image/png', 'image/jpg',
                'image/jpeg', 'image/pjpeg', 'image/gif'
            ]
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

            img_uuid = "{0}-{1}".format(uuid.uuid4().hex[:10], image.name.replace(' ', '-'))
            tmp_file = os.path.join(settings.MARTOR_UPLOAD_PATH, img_uuid)
            def_path = default_storage.save(tmp_file, ContentFile(image.read()))
            img_url = os.path.join(settings.MEDIA_URL, def_path)

            data = json.dumps({
                'status': 200,
                'link': img_url,
                'name': image.name
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
def cycle_donatoins_list(request):
    if request.method == 'GET':
        cycle_donations = CycleDonation.objects.all()
        serializer = CycleDonationSerializer(cycle_donations, many=True)
        return Response(serializer.data)


@api_view(['POST'])
def cycle_add_segment(request):
    if request.method == 'POST':
        serializer = SegmentSerializer(data=request.data)
        if serializer.is_valid():
            segment = serializer.save()
            cycle_donatoins_serializer = CycleDonationSerializer(segment.get_cycle_donations(), many=True)

            return Response(cycle_donatoins_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
