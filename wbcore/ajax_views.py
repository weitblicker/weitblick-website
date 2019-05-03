from wbcore.serializers import NewsPostSerializer, BlogPostSerializer, HostSerializer, EventSerializer, ProjectSerializer
from wbcore.models import NewsPost, BlogPost, Host, Event, Project
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.template import loader
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
import csv


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

    result_groups = {'results': {},
        "action": {
            "url": '/search/'+query,
            "text": "View all results"
        }
    }

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
            cnt += 1
        result_groups['results'][str(key.get_model_name())] = {
            'name': str(key.get_model_name()),
            'results': result_set,
        }
    print("Found %s results in %s categories." % (cnt, len(result_groups)))

    return JsonResponse(result_groups)


@api_view(['GET', 'POST'])
def filter_news(request):

    template = loader.get_template('wbcore/news_list.html')
    host_slugs = request.GET.getlist("union")
    contains = request.GET.get("contains")
    host_slugs = list(csv.reader(host_slugs))
    host_slugs = list(set().union(*host_slugs))
    host_slugs = [x.strip(' ') for x in host_slugs]

    host_slug = None

    try:
        #posts = NewsPost.objects.filter(host__slug__in=host_slugs).distinct()
        host = Host.objects.get(slug=host_slug) if host_slug else None
        print("Host Slugs", host_slugs)
        
        results = SearchQuerySet()
        if host_slugs:
            results = results.filter_or(host_slug__in=host_slugs)

        results = results.filter_and(content__contains=contains)
        results = results.models(NewsPost).order_by('-published')[:20]

        print("Length:", len(results))
        posts = [result.object for result in results]
        
    except Host.DoesNotExist:
        raise Http404()

    context = {
        'posts': posts,
        'host': host,
    }
    return HttpResponse(template.render(context, request))
