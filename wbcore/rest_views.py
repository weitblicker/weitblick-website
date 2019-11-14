from wbcore.serializers import (NewsPostSerializer, BlogPostSerializer, HostSerializer, EventSerializer,
                                ProjectSerializer, LocationSerializer)
from wbcore.models import NewsPost, BlogPost, Host, Event, Project, Location
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .filter import filter_events, filter_projects, filter_news, filter_blog

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


