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


def parse_categories(request):
    categories = request.GET.getlist("category")
    categories = list(csv.reader(categories))
    categories = categories[0] if len(categories) > 0 else []
    return categories

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

    events = results.models(Event)

    # search results for start and end date
    # handle cases where no dates are given
    if start and end:
        start_date = start
        end_date = end
    elif start:
        then = start.replace(year=start.year + 10)
        start_date = start
        end_date = then
    elif end:
        last_year = datetime.now() - relativedelta(years=1)
        start_date = last_year
        end_date = end
    else:
        last_year = datetime.now() - relativedelta(years=1)
        then = datetime.now().replace(year=last_year.year + 10)
        start_date = last_year
        end_date = then

    return events, start_date, end_date, limit


def filter_partners(request, default_limit=None):
    host_slugs = parse_union(request)
    contains = request.GET.get("search")
    active = request.GET.get("active")
    categories = parse_categories(request)
    limit = parse_limit(request, default=default_limit) if default_limit else parse_limit(request)

    results = SearchQuerySet()
    if host_slugs:
        results = results.filter(hosts_slug__in=host_slugs)
    if contains:
        results = results.filter_and(text__contains=contains)
    if categories:
        results = results.filter_and(category__in=categories)
    if active == 'active':
        results = results.filter_and(active=True)
    elif active == 'former':
        results = results.exclude(active=True)

    results = results.models(Partner).all()
    if limit:
        results = results[:limit]

    partners = [result.object for result in results]
    return partners


def reorder_inactive_partners(item_list):
    item_list_current = [item for item in item_list if item.active]
    item_list_passed = [item for item in item_list if not item.active]
    if item_list_passed:
        item_list_passed[0].first_passed_item = True
        item_list_passed[0].separator_text = _('Former')
    return item_list_current + item_list_passed
>>>>>>> master
