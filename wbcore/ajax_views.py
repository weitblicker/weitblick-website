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
from datetime import datetime, date, timedelta
from schedule.periods import Period
import csv
from .views import item_list_from_occ, item_list_from_blogposts


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
def filter_projects(request):

    template = loader.get_template('wbcore/projects_list.html')
    host_slugs = request.GET.getlist("union")
    contains = request.GET.get("search")
    country_codes = request.GET.getlist("country")
    visibility = request.GET.get("visibility")

    host_slugs = list(csv.reader(host_slugs))
    host_slugs = list(set().union(*host_slugs))
    host_slugs = [x.strip(' ') for x in host_slugs]

    country_codes = list(csv.reader(country_codes))
    country_codes = list(set().union(*country_codes))
    country_codes = [x.strip(' ') for x in country_codes]

    host_slug = None

    try:
        #posts = NewsPost.objects.filter(host__slug__in=host_slugs).distinct()
        host = Host.objects.get(slug=host_slug) if host_slug else None

        results = SearchQuerySet()
        if host_slugs:
            results = results.filter_or(hosts_slug__in=host_slugs)
        if visibility == 'completed':
            results = results.filter_and(completed=True)
        if visibility == 'current':
            results = results.exclude(completed=True)
        if country_codes:
            results = results.filter_and(country_code__in=country_codes)
        if contains:
            results = results.filter_and(text__contains=contains)

        results = results.models(Project).all()
        projects = [result.object for result in results]

    except Host.DoesNotExist:
        raise Http404()

    context = {
        'projects': projects,
        'host': host,
    }
    return HttpResponse(template.render(context, request))


@api_view(['GET', 'POST'])
def filter_news(request):

    template = loader.get_template('wbcore/item_list.html')
    host_slugs = request.GET.getlist("union")
    contains = request.GET.get("search")
    host_slugs = list(csv.reader(host_slugs))
    host_slugs = list(set().union(*host_slugs))
    host_slugs = [x.strip(' ') for x in host_slugs]

    archive = request.GET.get("archive")

    start = None
    end = None

    if archive:
        try:
            start = datetime.strptime(archive, '%Y-%m').date()
            if start.month is 12:
                end = date(start.year+1, 1, 1)
            else:
                end = date(start.year, start.month+1, 1)
        except ValueError:
            try:
                start = datetime.strptime(archive, '%Y').date()
                end = date(start.year+1, 1, 1)
            except ValueError:
                start = None
                end = None

    print("Date", start, end)
    print("Contains:", contains)
    host_slug = None

    try:
        #posts = NewsPost.objects.filter(host__slug__in=host_slugs).distinct()
        host = Host.objects.get(slug=host_slug) if host_slug else None
        print("Host Slugs", host_slugs)

        results = SearchQuerySet()
        if host_slugs:
            results = results.filter_or(host_slug__in=host_slugs)
        if contains:
            results = results.filter_and(content__contains=contains)
        if start:
            results = results.filter_and(published__lte=end)
            results = results.filter_and(published__gte=start)

        results = results.models(NewsPost).order_by('-published')[:20]

        print("Length:", len(results))
        posts = [result.object for result in results]

    except Host.DoesNotExist:
        raise Http404()

    context = {
        'posts': posts,
        'host': host,
        'item_list': posts,
    }
    return HttpResponse(template.render(context, request))

@api_view(['GET', 'POST'])
def filter_events(request):
    template = loader.get_template('wbcore/item_list.html')
    host_slugs = request.GET.getlist("union")
    contains = request.GET.get("search")
    host_slugs = list(csv.reader(host_slugs))
    host_slugs = list(set().union(*host_slugs))
    host_slugs = [x.strip(' ') for x in host_slugs]

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    start = None
    end = None

    # set start and end for search query
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m')
        except ValueError:
            try:
                start = datetime.strptime(start_date, '%Y')
            except ValueError:
                start = None
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m')
            if end.month == 12:
                end = end.replace(year=end.year+1, month=1)
            else:
                end = end.replace(month=end.month+1)
        except ValueError:
            try:
                end = datetime.strptime(end_date, '%Y')
                end = end.replace(year=end.year+1)
            except ValueError:
                end = None

    print("Date", start, '- ', end)
    print("Contains:", contains)
    host_slug = None

    try:
        #posts = Event.objects.filter(host__slug__in=host_slugs).distinct()
        host = Host.objects.get(slug=host_slug) if host_slug else None
        print("Host Slugs", host_slugs)

        results = SearchQuerySet()
        if host_slugs:
            results = results.filter_or(hosts_slug__in=host_slugs)
        if contains:
            results = results.filter_and(content__contains=contains)

        results = results.models(Event)
        print("Length:", len(results))

        # search results for start and end date
        # handle cases where no dates are given
        events = [result.object for result in results]
        if start and end:
            p = Period(events, start, end)
        if start:
            then = start.replace(year=start.year+10)
            p = Period(events, start, then)
        elif end:
            now = datetime.now()
            p = Period(events, now, end)
        else:
            now = datetime.now()
            then = datetime.now().replace(year=now.year+10)
            p = Period(events, now, then)
        occurrences = p.get_occurrences()[:20]

    except Host.DoesNotExist:
        raise Http404()

    context = {
        'item_list': item_list_from_occ(occurrences),
        'host': host,
    }
    return HttpResponse(template.render(context, request))

@api_view(['GET', 'POST'])
def filter_blog(request):
    template = loader.get_template('wbcore/item_list.html')
    host_slugs = request.GET.getlist("union")
    contains = request.GET.get("search")
    host_slugs = list(csv.reader(host_slugs))
    host_slugs = list(set().union(*host_slugs))
    host_slugs = [x.strip(' ') for x in host_slugs]

    archive = request.GET.get("archive")

    start = None
    end = None

    if archive:
        try:
            start = datetime.strptime(archive, '%Y-%m').date()
            end = date(start.year, start.month+1, 1) if start.month!=12 else date(start.year+1, 1, 1)
        except ValueError:
            try:
                start = datetime.strptime(archive, '%Y').date()
                end = date(start.year+1, 1, 1)
            except ValueError:
                start = None
                end = None

    print("Date", start, end)
    print("Contains:", contains)
    host_slug = None

    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
        print("Host Slugs", host_slugs)

        results = SearchQuerySet()
        if host_slugs:
            results = results.filter_or(host_slug__in=host_slugs)
        if contains:
            results = results.filter_and(content__contains=contains)
        if start:
            results = results.filter_and(published__lte=end)
            results = results.filter_and(published__gte=start)
        results = results.models(BlogPost).order_by('-published')[:20]

        print("Length:", len(results))
        posts = [result.object for result in results]

    except Host.DoesNotExist:
        raise Http404()

    context = {
        'host': host,
        'item_list': item_list_from_blogposts(posts, host_slug),
    }
    return HttpResponse(template.render(context, request))
