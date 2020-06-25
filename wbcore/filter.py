import csv
from datetime import datetime, timezone, date
from haystack.query import SearchQuerySet
from wbcore.models import NewsPost, BlogPost, Project, Event, Partner
from schedule.periods import Period
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.utils.translation import ugettext as _


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


def parse_filter_date(request):
    start_str = request.GET.get('from')
    end_str = request.GET.get('to')

    start = None
    end = None

    if start_str:
        try:
            start = parse(start_str + '-01')
        except ValueError:
            pass

    if end_str:
        try:
            end = parse(end_str + '-01') + relativedelta(months=1)  # include the selected month
        except ValueError:
            pass

    return start, end


def filter_projects(request, default_limit=None):
    host_slugs = parse_union(request)
    contains = request.GET.get("search")
    visibility = request.GET.get("visibility")
    country_codes = parse_country(request)
    limit = parse_limit(request, default=default_limit) if default_limit else parse_limit(request)
    start, end = parse_filter_date(request)


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
    start, end = parse_filter_date(request)

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
    start, end = parse_filter_date(request)
    limit = parse_limit(request, default=default_limit) if default_limit else parse_limit(request)

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
    start, end = parse_filter_date(request)
    limit = parse_limit(request, default=default_limit) if default_limit else parse_limit(request)

    results = SearchQuerySet()
    if host_slugs:
        results = results.filter_or(hosts_slug__in=host_slugs)
    if contains:
        results = results.filter_and(content__contains=contains)

    results = results.models(Event)

    # search results for start and end date
    # handle cases where no dates are given
    events = [result.object for result in results]
    if start and end:
        p = Period(events, start, end)
    elif start:
        then = start.replace(year=start.year + 10)
        p = Period(events, start, then)
    elif end:
        now = datetime.now() - relativedelta(years=1)
        p = Period(events, now, end)
    else:
        now = datetime.now() - relativedelta(years=1)
        then = datetime.now().replace(year=now.year + 10)
        p = Period(events, now, then)

    occurrences = p.get_occurrences()

    if limit:
        occurrences = occurrences[:limit]

    return occurrences, events


def filter_partners(request, default_limit=None):
    host_slugs = parse_union(request)
    contains = request.GET.get("search")
    # status = request.GET.get("status")
    # category = request.GET.get("category")
    limit = parse_limit(request, default=default_limit) if default_limit else parse_limit(request)

    results = SearchQuerySet()
    if host_slugs:
        results = results.filter(hosts_slug__in=host_slugs)
    if contains:
        results = results.filter_and(text__contains=contains)
    # if category:
    #     results = results.filter_and(category=category)
    # if status == 'active':
    #     results = results.filter_and(active=True)
    # if status == 'active':
    #     results = results.filter_and(active=False)
    results.exclude(public=False)

    results = results.models(Partner).all()
    if limit:
        results = results[:limit]

    partners = [result.object for result in results]
    return partners


def reorder_completed_projects(item_list):
    item_list_current = [item for item in item_list if not item.completed]
    item_list_passed = [item for item in item_list if item.completed]
    if item_list_passed:
        item_list_passed[0].first_passed_item = True
        item_list_passed[0].separator_text = _('Completed')
    return item_list_current + item_list_passed


def reorder_passed_events(item_list):
    item_list_current = [item for item in item_list if item.end > datetime.now(timezone.utc)]
    item_list_passed = [item for item in item_list if item.end <= datetime.now(timezone.utc)][::-1]
    if item_list_passed:
        item_list_passed[0].first_passed_item = True
        item_list_passed[0].separator_text = _('Previous')
    return item_list_current + item_list_passed