import csv
from datetime import datetime, date, timedelta
from haystack.query import SearchQuerySet
from .models import NewsPost, BlogPost, Project, Event
from schedule.periods import Period
from dateutil.parser import parse

def parse_union(request):
    host_slugs = request.GET.getlist("union")
    host_slugs = list(csv.reader(host_slugs))
    host_slugs = list(set().union(*host_slugs))
    host_slugs = [x.strip(' ') for x in host_slugs]
    return host_slugs


def parse_country(request):
    country_codes = request.GET.getlist("country")
    country_codes = list(csv.reader(country_codes))
    country_codes = list(set().union(*country_codes))
    country_codes = [x.strip(' ') for x in country_codes]
    return country_codes


def parse_limit(request, default=20):
    limit_str = request.GET.get('limit')
    limit = default
    if limit_str:
        try:
            limit = int(limit_str)
        except ValueError:
            pass

    if limit is -1:
        return None

    return limit


def parse_archive_start_end(request):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    start = None
    end = None

    if start_str:
        try:
            start = parse(start_str)
        except ValueError:
            pass

    if end_str:
        try:
            end = parse(end_str)
        except ValueError:
            pass

    if start or end:
        return start, end

    archive = request.GET.get("archive")

    if archive:
        try:
            start = datetime.strptime(archive, '%Y-%m').date()
            if start.month is 12:
                end = date(start.year + 1, 1, 1)
            else:
                end = date(start.year, start.month + 1, 1)
        except ValueError:
            try:
                start = datetime.strptime(archive, '%Y').date()
                end = date(start.year + 1, 1, 1)
            except ValueError:
                start = None
                end = None

    return start, end


def filter_projects(request, default_limit=None):
    host_slugs = parse_union(request)
    contains = request.GET.get("search")
    visibility = request.GET.get("visibility")
    country_codes = parse_country(request)
    limit = parse_limit(request, default=default_limit) if default_limit else parse_limit(request)
    start, end = parse_archive_start_end(request)

    print("Start:", start, "End:", end)

    results = SearchQuerySet()
    if host_slugs:
        results = results.filter(hosts_slug__in=host_slugs)
    if visibility == 'completed':
        results = results.filter_and(completed=True)
    elif visibility == 'current':
        results = results.exclude(completed=True)
    if country_codes:
        results = results.filter_and(country_code__in=country_codes)
    if contains:
        results = results.filter_and(text__contains=contains)
    if start:
        results &= SearchQuerySet().filter(start_date__gte=start) | SearchQuerySet().filter(end_date__gte=start)
    if end:
        results &= SearchQuerySet().filter(start_date__lt=end) | SearchQuerySet().filter(end_date__lt=end)

    results = results.models(Project).all()
    if limit:
        results = results[:limit]

    projects = [result.object for result in results]
    return projects


def filter_news(request, default_limit=None):
    # read hosts list or single
    host_slugs = parse_union(request)
    contains = request.GET.get("search")
    limit = parse_limit(request, default=default_limit) if default_limit else parse_limit(request)
    start, end = parse_archive_start_end(request)

    results = SearchQuerySet()

    if host_slugs:
        results = results.filter_or(host_slug__in=host_slugs)
    if contains:
        results = results.filter_and(content__contains=contains)
    if start:
        results = results.filter_and(published__gte=start)
    if end:
        results = results.filter_and(published__lt=end)

    results = results.models(NewsPost).order_by('-published')
    if limit:
        results = results[:limit]

    posts = [result.object for result in results]
    return posts


def filter_blog(request, default_limit=None):
    host_slugs = parse_union(request)
    contains = request.GET.get("search")
    start, end = parse_archive_start_end(request)
    limit = parse_limit(request, default=default_limit) if default_limit else parse_limit(request)

    print("Date", start, end)
    print("Contains:", contains)

    results = SearchQuerySet()
    if host_slugs:
        results = results.filter_or(host_slug__in=host_slugs)
    if contains:
        results = results.filter_and(content__contains=contains)
    if start:
        results = results.filter_and(published__gte=start)
    if end:
        results = results.filter_and(published__lt=end)

    results = results.models(BlogPost).order_by('-published')
    if limit:
        results = results[:limit]

    return [result.object for result in results]


def filter_events(request, default_limit=None):
    host_slugs = parse_union(request)
    contains = request.GET.get("search")
    start, end = parse_archive_start_end(request)
    limit = parse_limit(request, default=default_limit) if default_limit else parse_limit(request)

    print("Date", start, '- ', end)
    print("Contains:", contains)

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
    elif start:
        then = start.replace(year=start.year + 10)
        p = Period(events, start, then)
    elif end:
        now = datetime.now()
        p = Period(events, now, end)
    else:
        now = datetime.now()
        then = datetime.now().replace(year=now.year + 10)
        p = Period(events, now, then)

    occurrences = p.get_occurrences()

    if limit:
        occurrences = occurrences[:limit]

    return occurrences, events
