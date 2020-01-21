from django.http import HttpResponse, JsonResponse
from django.template import loader
from rest_framework.decorators import api_view
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery, Exact, Clean
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from itertools import groupby
from .filter import filter_news, filter_projects, filter_events
from .views import item_list_from_occ, item_list_from_posts, item_list_from_proj


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
def filter_projects_view(request, host_slug=None):
    template = loader.get_template('wbcore/list_items.html')
    projects = filter_projects(request)
    host = None  # TODO filter if on host specific news page
    context = {
        'host': host,
        'item_list': item_list_from_proj(projects, host_slug)
    }
    return HttpResponse(template.render(context, request))


@api_view(['GET', 'POST'])
def filter_news_view(request):
    template = loader.get_template('wbcore/list_items.html')
    posts = filter_news(request, default_limit=-1)
    host = None  # TODO filter if on host specific news page
    context = {
        'host': host,
        'item_list': posts,
    }
    return HttpResponse(template.render(context, request))


@api_view(['GET', 'POST'])
def filter_events_view(request):
    template = loader.get_template('wbcore/list_items.html')
    event_occurrences, events = filter_events(request)
    host = None  # TODO filter if on host specific news page
    context = {
        'item_list': item_list_from_occ(event_occurrences),
        'host': host,
    }
    return HttpResponse(template.render(context, request))


@api_view(['GET', 'POST'])
def filter_blog_view(request):
    template = loader.get_template('wbcore/list_items.html')
    host = None  # TODO filter if on host specific news page
    context = {
        'host': host,
        'item_list': item_list_from_posts(posts, host_slug=host_slug, post_type="blog-post", id_key='post_id'),
    }
    return HttpResponse(template.render(context, request))
