from wbcore.serializers import NewsPostSerializer, BlogPostSerializer, HostSerializer, EventSerializer, ProjectSerializer
from wbcore.models import NewsPost, BlogPost, Host, Event, Project
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.postgres.search import SearchVector
from django.urls import reverse
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery, Exact, Clean
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from itertools import groupby

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
        events = Event.objects.all()
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
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data)


@api_view(['GET'])
def project_detail(request, pk, format=None):
    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProjectSerializer(project)
        return Response(serializer.data)


@api_view(['GET'])
def post_list(request, format=None):
    if request.method == 'GET':
        posts = NewsPost.objects.all()
        serializer = NewsPostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


@api_view(['GET'])
def post_detail(request, pk, format=None):
    try:
        post = NewsPost.objects.get(pk=pk)
    except NewsPost.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = NewsPostSerializer(post)
        return Response(serializer.data)



def remove_tags(text):
    from tidylib import tidy_fragment

    import re, html
    text = html.unescape(text)
    text, errors = tidy_fragment(text)
    tag_re = re.compile(r'<[^>]+>')
    return tag_re.sub('', text)


@api_view(['GET', 'POST'])
def search(request, query):

    results = SearchQuerySet().filter(content__contains=query).highlight()

    result_groups = {'results': {}}

    cnt = 0
    for key, group in groupby(results, lambda x: x.model):
        result_set = []
        for result in group:
            elem = {
                'title': result.object.search_title(),
                'description': remove_tags(result.highlighted[0]),
                'url': result.object.search_url(),
                'image': result.object.search_image(),
            }
            result_set.append(elem);
            if len(result_set) > 2:
                break
            cnt = cnt + 1
        result_groups['results'][str(key.get_model_name())] = {
            'name': str(key.get_model_name()),
            'results': result_set,
        }
    print("Found %s results in %s categories." % (cnt, len(result_groups)))

    return JsonResponse(result_groups)

