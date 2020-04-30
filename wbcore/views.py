import csv

from django.utils.translation import gettext as _
from django.db.models import Count
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader, RequestContext
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth import login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.sites.models import Site

from collections import OrderedDict
from datetime import date, datetime, timedelta
from schedule.periods import Period
import locale

from wbcore.tokens import account_activation_token

from wbcore.forms import (
    ContactForm, UserForm, BankForm, UserRelationForm, AddressForm, User)

from wbcore.models import (
    Host, Project, Event, NewsPost, Location, BlogPost, Team, TeamUserRelation,
    UserRelation, JoinPage, SocialMediaLink, Content, Document, Donation, FAQ)

main_host_slug = 'bundesverband' ## TODO configure this?

icon_links = OrderedDict([
    ('facebook',
        {'name': 'Facebook',
         'link': 'https://www.facebook.com/weitblick/',
         'icon': 'facebook f'}),
    ('twitter',
        {'name': 'Twitter',
         'link': 'https://twitter.com/weitblick',
         'icon': 'twitter'}),
    ('instagram',
        {'name': 'Instagram',
         'link': 'https://www.instagram.com/weitblick_e.v/',
         'icon': 'instagram'}),
    ('youtube',
        {'name': 'YouTube',
         'link': 'https://www.youtube.com/user/weitblickTV',
         'icon': 'youtube'}),
    ('soundcloud',
        {'name': 'SoundCloud',
         'link': 'https://soundcloud.com/weitblick',
         'icon': 'soundcloud'}),
    ('email',
        {'name': 'E-Mail',
         'link': 'mailto:info@weitblicker.org',
         'icon': 'envelope outline'}),
    ('login',
        {'name': 'Login',
         'link': '/admin/login/',
         'icon': 'unlock alternate'}),
])


def get_main_nav(host=None, active=None):
    args = [host.slug] if host else []
    nav = OrderedDict([
            ('home',
                {
                    'name': _('Home'),
                    'link': reverse('home'),
                    'icon': 'wbcore/svgs/home.svg',
                    'mobile': False,
                }),
            ('idea',
                {
                    'name': _('Idea'),
                    'link': reverse('idea', args=args),
                    'icon': 'wbcore/svgs/idea.svg',
                    'mobile': True,
                }),
            ('projects',
                {
                    'name': _('Projects'),
                    'link': reverse('projects', args=args),
                    'icon': 'wbcore/svgs/leaf.svg',
                    'mobile': True,
                }),
            ('events',
                {
                    'name': _('Events'),
                    'link': reverse('events', args=args),
                    'icon': 'wbcore/svgs/hand.svg',
                    'mobile': True,
                }),
            ('join',
                {
                    'name': _('Participate'),
                    'link': reverse('join', args=args),
                    'icon': 'wbcore/svgs/people.svg',
                    'mobile': True,
                }),
            ('hosts',
                {
                    'name': _('Associations'),
                    'link': reverse('hosts'),
                    'icon': 'wbcore/svgs/unions.svg',
                    'mobile': True,
                }),
    ])

    if active in nav:
        nav[active]['link'] = None

    return nav


def get_dot_nav(host=None):
    if host:
        news = NewsPost.objects.filter(host=host).order_by('-published')[:3]
        blog = BlogPost.objects.filter(host=host).order_by('-published')[:3]
        occurences = Period(Event.objects.filter(host=host), datetime.now(), datetime.now() + timedelta(days=365)).get_occurrences()[:3]
    else:
        news = NewsPost.objects.all().order_by('-published')[:3]
        blog = BlogPost.objects.all().order_by('-published')[:3]
        occurences = Period(Event.objects.all(), datetime.now(), datetime.now() + timedelta(days=365)).get_occurrences()[:3]
    events = [occ.event for occ in occurences]
    for event in events:
        if event.start.day == event.end.day:
            event.show_date = event.start.strftime('%a, %d. %b %Y')
            event.show_date += "<br>" + event.start.strftime('%H:%M') + " - " + event.end.strftime('%H:%M')
        else:
            event.show_date = event.start.strftime('%a, %d. %b')
            event.show_date += " -<br>" + event.end.strftime('%a, %d. %b %Y')
    return {'news': news, 'blog': blog, 'events': events}


def get_host_slugs(request, host_slug):
    if host_slug:
        host_slugs = [host_slug]
    else:
        host_slugs = request.GET.getlist("union")
        host_slugs = list(csv.reader(host_slugs))
        host_slugs = list(set().union(*host_slugs))
        host_slugs = [x.strip(' ') for x in host_slugs]
    return host_slugs


def item_list_from_occ(occurrences, host_slug=None, text=True):
    # set attributes to fill list_item template
    item_list = []
    for occ in occurrences:
        occ.image = occ.event.image
        locale.setlocale(locale.LC_ALL, "de_DE")
        if occ.start.day == occ.end.day:
            occ.show_date = occ.start.strftime('%a, %d. %b %Y')
        else:
            occ.show_date = occ.start.strftime('%d. %b') + " - " + occ.end.strftime('%d. %b %Y')
        occ.host = occ.event.host
        current_host = Host.objects.get(slug=host_slug) if host_slug else None
        if current_host and current_host == occ.event.host:
            occ.link = reverse('event', kwargs={'event_slug': occ.event.slug, 'host_slug': host_slug})
        else:
            occ.link = reverse('event', args=[occ.event.slug])
        if text:
            occ.teaser = occ.event.teaser if occ.event.teaser else occ.description
        else:
            occ.teaser = ""
        occ.show_text = text
        item_list.append(occ)
    return item_list


def item_list_from_posts(posts, host_slug=None, post_type='news-post', id_key='post_id', text=True):

    item_list = []
    for post in posts:
        if not post.teaser:
            post.teaser = post.text

        if not text:
            post.teaser = ""
        current_host = Host.objects.get(slug=host_slug) if host_slug else None
        if current_host and post.host and current_host == post.host:
            post.link = reverse(post_type, kwargs={id_key: post.id, 'host_slug': host_slug})

        else:
            post.link = reverse(post_type, args=[post.id])
        post.show_text = text
        post.image = post.get_title_image()
        item_list.append(post)
    return item_list


def item_list_from_proj(projects, host_slug=None, text=True):
    item_list = []
    for project in projects:
        project.image = project.get_title_image()
        project.country = project.location.country.name
        project.published = None  # do not show published date, but rather if active or not
        project.hosts_list = project.hosts.all()
        current_host = Host.objects.get(slug=host_slug) if host_slug else None
        if current_host and current_host in project.hosts.all():
            project.link = reverse('project', kwargs={'project_slug': project.slug, 'host_slug': host_slug})
        else:
            project.link = reverse('project', args=[project.slug])
        project.title = project.name
        project.teaser = project.short_description if project.short_description else project.description
        project.show_text = True if text else False
        item_list.append(project)
    return item_list

def item_list_from_teams(teams, host_slug=None):
    item_list = []
    for team in teams:
        team.title = team.name
        team.teaser = team.teaser if team.teaser else team.description
        team.image = team.image
        print("***", team.image)
        team.country = None
        team.published = None
        team.hosts_list = [team.host]
        if host_slug:
            team.link = reverse('team', kwargs={'team_slug': team.slug, 'host_slug': host_slug})
        else:
            team.link = reverse('team', kwargs={'team_slug': team.slug})
        item_list.append(team)
    return item_list


def home_view(request):
    projects = Project.objects.all()
    hosts = Host.objects.all()
    news = NewsPost.objects.all().order_by('-published')[:5]
    blog = BlogPost.objects.all().order_by('-published')[:3]
    events = Event.objects.all().order_by('-start')
    period = Period(events, datetime.now(), datetime.now() + timedelta(365/2))
    occurrences = period.get_occurrences()[:3]


    template = loader.get_template('wbcore/home.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(),
        'projects': projects,
        'blog_item_list': item_list_from_posts(blog, post_type='blog-post', id_key='post_id', text=False),
        'news_item_list': item_list_from_posts(news, post_type='news-post', id_key='news_id'),
        'hosts': hosts,
        'event_item_list': item_list_from_occ(occurrences, text=True),
        'breadcrumb': [(_('Home'), None)],
        'icon_links': icon_links
    }



    return HttpResponse(template.render(context, request))


def reports_view(request, host_slug=None):
    if host_slug:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Reports'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Reports'), None)]

    load_host = host if host else Host.objects.get(slug='bundesverband')
    try:
        report = Content.objects.get(host=load_host, type='reports')
    except Content.DoesNotExist:
        report = None
    financial_reports = Document.objects.filter(host=load_host, document_type='financial_report', public=True)
    financial_reports = financial_reports.order_by('-valid_from') if financial_reports else financial_reports
    annual_reports = Document.objects.filter(host=load_host, document_type='annual_report', public=True)
    annual_reports = annual_reports.order_by('-valid_from') if annual_reports else annual_reports

    template = loader.get_template('wbcore/reports.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'report': report,
        'financial_reports': financial_reports,
        'annual_reports': annual_reports,
    }
    return HttpResponse(template.render(context, request))


def charter_view(request, host_slug=None):
    if host_slug:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Charter'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Charter'), None)]

    load_host = host if host else Host.objects.get(slug='bundesverband')
    try:
        charter = Content.objects.get(host=load_host, type='charter')
    except Content.DoesNotExist:
        charter = None

    charter_files = Document.objects.filter(host=load_host, document_type='charter', public=True)
    charter_files = charter_files.order_by('valid_from') if charter_files else charter_files

    template = loader.get_template('wbcore/charter.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'charter': charter,
        'hosts': Host.objects.all(),
        'charter_files': charter_files,
    }
    return HttpResponse(template.render(context, request))


def transparency_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Transparency'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Transparency'), None)]

    load_host = host if host else Host.objects.get(slug='bundesverband')
    try:
        transparency = Content.objects.get(host=load_host, type='transparency')
    except Content.DoesNotExist:
        transparency = None

    transparency_data = {
        "host_name": load_host.charter_name if load_host.charter_name else load_host.name,
        "founding_date": load_host.founding_date,
        "tax_exemption_notice_date": load_host.tax_exemption_notice_date,
        "major_donations": Donation.objects.filter(host=load_host, major_donation=True).order_by("-amount"),  # for last calendar year date__year=datetime.now().year - 1
    }

    financial_reports = Document.objects.filter(host=load_host, document_type='financial_report', public=True)
    financial_reports = financial_reports.order_by('valid_from') if financial_reports else financial_reports
    annual_reports = Document.objects.filter(host=load_host, document_type='annual_report', public=True)
    annual_reports = annual_reports.order_by('valid_from') if annual_reports else annual_reports


    template = loader.get_template('wbcore/transparency.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'host_url_prefix': "/" + host.slug + "/" if host else "/",
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'transparency': transparency,
        'transparency_data': transparency_data,
        'hosts': Host.objects.all(),
        'financial_reports': financial_reports,
        'annual_reports': annual_reports,
    }
    return HttpResponse(template.render(context, request))


def facts_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Facts'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Facts'), None)]

    load_host = Host.objects.get(slug=host_slug) if host_slug else Host.objects.get(slug='bundesverband')
    try:
        facts = Content.objects.get(host=load_host, type='facts')
    except Content.DoesNotExist:
        facts = None

    template = loader.get_template('wbcore/facts.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'facts': facts,
    }
    return HttpResponse(template.render(context, request))


def history_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('History'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('History'), None)]

    load_host = host if host else Host.objects.get(slug='bundesverband')
    try:
        history = Content.objects.get(host=load_host, type='history')
    except Content.DoesNotExist:
        history = None

    if host_slug:
        projects = Project.objects.filter(hosts__slug=host_slug)[:3]
    else:
        projects = Project.objects.all()[:3]

    template = loader.get_template('wbcore/history.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'history': history,
        'hosts': Host.objects.all(),
        'project_item_list': item_list_from_proj(projects, host_slug),
    }
    return HttpResponse(template.render(context, request))


def privacy_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Privacy'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Privacy'), None)]

    load_host = Host.objects.get(slug=host_slug) if host_slug else Host.objects.get(slug='bundesverband')
    try:
        privacy = Content.objects.get(host=load_host, type='privacy')
    except Content.DoesNotExist:
        privacy = None

    template = loader.get_template('wbcore/privacy.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'privacy': privacy,
        'hosts': Host.objects.all(),
    }
    return HttpResponse(template.render(context, request))


def teams_view(request, host_slug=None):
    try:
        if host_slug:
            host = Host.objects.get(slug=host_slug)
        else:
            host = None
    except Host.DoesNotExist:
        raise Http404()
    if host:
        try:
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Team'), None)]
            teams = Team.objects.filter(host=host)
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Team'), None)]
        teams = Team.objects.filter(host=Host.objects.get(slug='bundesverband'))

    projects = Project.objects.filter(hosts=host).order_by('-published') if host else Project.objects.all().order_by('-published')
    projects = projects[:3]

    template = loader.get_template('wbcore/teams.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'item_list': item_list_from_teams(teams, host_slug),
        'icon_links': icon_links,
        'hosts': Host.objects.all(),
        'project_item_list': item_list_from_proj(projects, host_slug),
    }
    return HttpResponse(template.render(context, request))


def team_view(request, host_slug=None, team_slug=None):
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
    except Host.DoesNotExist:
        raise Http404()

    try:
        if host:
            team = Team.objects.get(slug=team_slug, host=host)
        else:
            team = Team.objects.get(slug=team_slug, host=Host.objects.get(slug='bundesverband'))
    except Team.DoesNotExist:
        raise Http404()

    if host:
        breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Team'), reverse('teams')), (team.name, None)]
    else:
        breadcrumb = [(_('Home'), reverse('home')), (_('Team'), reverse('teams')), (team.name, None)]

    relations = team.teamuserrelation_set.all().order_by('priority')

    teams = Team.objects.filter(host=host) if host else Team.objects.filter(host__slug=main_host_slug)
    projects = Project.objects.filter(hosts=host) if host else Project.objects.all()
    teams, projects = teams[:3], projects[:3]

    template = loader.get_template('wbcore/team.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'team': team,
        'members_relations': relations,
        'icon_links': icon_links,
        'hosts': Host.objects.all() if host_slug in [None, 'bundesverband'] else None,
        'teams': item_list_from_teams(teams, host_slug),
        'project_item_list': item_list_from_proj(projects, host_slug)
    }
    return HttpResponse(template.render(context, request))


def about_view(request, host_slug=None):

    if not host_slug:
        host_slug = main_host_slug

    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
        breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('About'), None)]
    except:
        raise Http404()

    breadcrumb = [(_('Home'), reverse('home')), (_('About'), None)]

    try:
        about = Content.objects.get(host=host, type='about')
    except Content.DoesNotExist:
        about = None

    news = NewsPost.objects.all().order_by('-published')[:3]
    blog = BlogPost.objects.all().order_by('-published')[:3]
    events = Event.objects.all().order_by('-start')
    period = Period(events, datetime.now() - timedelta(hours=2), datetime.now() + timedelta(365/2))
    occurrences = period.get_occurrences()[:3]

    template = loader.get_template('wbcore/about.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'about': about,
        'hosts': Host.objects.all(),
        'blog_item_list': item_list_from_posts(blog, post_type='blog-post', id_key='post_id'),
        'news_item_list': item_list_from_posts(news, post_type='news-post', id_key='news_id'),
        'event_item_list': item_list_from_occ(occurrences, text=True),
    }
    return HttpResponse(template.render(context, request))


def idea_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)
    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Idea'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Idea'), None)]

    projects = Project.objects.all()
    project_item_list = item_list_from_proj(projects, host_slug)[:3]

    try:
        idea = Content.objects.get(host=Host.objects.get(slug='bundesverband'), type='idea')
    except Content.DoesNotExist as e:
        idea = None

    template = loader.get_template('wbcore/idea.html')
    context = {
        'main_nav': get_main_nav(active='idea', host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'idea': idea,
        'breadcrumb': breadcrumb,
        'hosts': Host.objects.all(),
        'project_item_list': project_item_list,
    }
    return HttpResponse(template.render(context, request))


def projects_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            projects = Project.objects.filter(hosts__slug__in=host_slugs).distinct()
            breadcrumb = [(_('Home'), reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          (_('Projects'), None)]
        except Host.DoesNotExist:
            raise Http404()
    else:
        host = None
        projects = Project.objects.all()
        breadcrumb = [(_('Home'), reverse('home')), (_('Projects'), None)]

    # sort projects
    if host_slug or len(host_slugs) == 1:  # only order by priority in host view to avoid competition between hosts
        projects = projects.order_by('-priority', '-updated')
    else:
        projects = projects.order_by('-updated')

    posts = BlogPost.objects.filter(project__in=projects)

    countries = set([project.location.country for project in projects])

    project_list = list(Location.objects.filter(project__in=projects).values(
            'country').annotate(number=Count('country')))

    hosts = Host.objects.all()

    if request.is_ajax():
        template = loader.get_template('wbcore/list_items.html')
    else:
        template = loader.get_template('wbcore/projects.html')
    context = {
        'main_nav': get_main_nav(host=host, active='projects'),
        'dot_nav': get_dot_nav(host=host),
        'breadcrumb': breadcrumb,
        'item_list': item_list_from_proj(projects, host_slug),
        'project_list': project_list,
        'host': host,
        'filter_preset': {'host': [host.slug] if host else None, },
        'hosts': hosts,
        'posts': posts,
        'countries': countries,
        'filter_visibility': True,
        'ajax_endpoint': reverse('ajax-filter-projects'),
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def signup(user, host):
    subject = 'Mitgliedsantrag ' + host.name
    message = loader.render_to_string('wbcore/activation_email.html', {
        'domain': Site.objects.get_current().domain,
        'user': user,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'icon_links': icon_links,
    })
    email = EmailMessage(body=message, subject=subject, to=[user.email], reply_to=[host.email])
    email.send()


def activate_user(request, uidb64, token):

    pswd_form = None
    template = loader.get_template('wbcore/user_activation.html')
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        invalid = False
        success = False
        message = ""
        if not user.is_active:
            if request.method == 'POST':
                pswd_form = SetPasswordForm(user, request.POST)

                if pswd_form.is_valid():
                    pswd_form.save()
                    user.is_active = True
                    user.save()
                    success = True
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            else:
                pswd_form = SetPasswordForm(user)

        else:
            message = "The user has been activated already!"
            invalid = True
            success = False
    else:
        message = "The activation link is not valid!"
        invalid = True
        success = False

    context = {
        'invalid': invalid,
        'message': message,
        'success': success,
        'user': user,
        'pswd_form': pswd_form,
        'icon_links': icon_links,
        'submit_url': reverse('activate', args=[uidb64, token])
    }

    return HttpResponse(template.render(context, request))


def join_view(request, host_slug=None):
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
    except Host.DoesNotExist:
        raise Http404()

    template = loader.get_template('wbcore/join.html')
    join_page = None

    if host:
        breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Participate'), None)]
        submit_url = reverse('join', args=[host_slug])
    else:
        submit_url = reverse('join')
        breadcrumb = [(_('Home'), reverse('home')), (_('Participate'), None)]
        try:
            host = Host.objects.get(slug=main_host_slug)
        except Host.DoesNotExist:
            host = None

    # TODO join form disabled until privacy issues are sorted
    try:
        # join_page = host.joinpage
        join_page = None
    except JoinPage.DoesNotExist:
        pass

    success = False

    if request.method == 'POST':
        addr_form = AddressForm(request.POST)
        urel_form = UserRelationForm(request.POST)
        user_form = UserForm(request.POST)
        bank_form = BankForm(request.POST)
        pswd_form = SetPasswordForm(request.POST)

        host_matches = "host" in request.POST and request.POST["host"] == host_slug

        if all([host_matches,
                user_form.is_valid(),
                bank_form.is_valid(),
                urel_form.is_valid(),
                addr_form.is_valid()]):

            addr = addr_form.save()

            user = user_form.save(commit=False)
            user.address = addr
            user.save()

            addr.name = user.name()
            addr.save()

            urel = urel_form.save(commit=False)
            urel.user = user
            urel.save()

            bank = bank_form.save(commit=False)
            bank.profile = user
            bank.save()

            signup(user, host)

            success = True
    else:
        if host:
            urel_form = UserRelationForm(initial={'host': host_slug})
        else:
            urel_form = UserRelationForm()

        addr_form = AddressForm()
        user_form = UserForm()
        bank_form = BankForm()

    load_host = host if host else Host.objects.get(host_slug='bundesverband')
    projects = Project.objects.filter(hosts=load_host)[:3]
    membership_declaration = Document.objects.filter(host=host, document_type='membership_declaration', public=True).order_by('-valid_from') if host else None

    context = {
        'main_nav': get_main_nav(host=host, active='join'),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'success': success,
        'membership_declaration': membership_declaration,
        'icon_links': icon_links,
        'hosts': Host.objects.all() if host == Host.objects.get(slug='bundesverband') else None,
        'project_item_list': item_list_from_proj(projects, host_slug),
    }

    if join_page:
        context['image'] = join_page.image
        context['sepa_text'] = join_page.sepa_text
        context['text'] = join_page.text
        context['user_form'] = user_form
        context['bank_form'] = bank_form
        context['urel_form'] = urel_form
        context['addr_form'] = addr_form
        context['submit_url'] = submit_url
        context['enable_form'] = join_page.enable_form
    else:  # join Content text if form disabled
        load_host = host if host else Host.objects.get(slug='bundesverband')
        try:
            context['text'] = Content.objects.get(host=load_host, type="join").text
        except Content.DoesNotExist:
            pass

    return HttpResponse(template.render(context, request))


def project_view(request, host_slug=None, project_slug=None):

    try:
        if host_slug:
            project = Project.objects.get(slug=project_slug, hosts__slug=host_slug)
            host = Host.objects.get(slug=host_slug)
            breadcrumb = [(_('Home'), reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          (_('Projects'), reverse('projects')),
                          (project.name, None)]
        else:
            project = Project.objects.get(slug=project_slug)
            host = None
            breadcrumb = [(_('Home'), reverse('home')), (_('Projects'), reverse('projects')), (project.name, None)]
    except Project.DoesNotExist:
        raise Http404("Project does not exist!")
    except Host.DoesNotExist:
        raise Http404("Host does not exist!")

    project.image = project.get_title_image()

    if Event.objects.filter(projects=project).exists():
        events = Event.objects.filter(projects=project)
    else:
        events = Event.objects.filter(host=host if host else Host.objects.get(slug='bundesverband'))
    period = Period(events, datetime.now(), datetime.now() + timedelta(365/2))
    occurrences = period.get_occurrences()[:3]

    news = NewsPost.objects.filter(project=project).order_by('-published')[:3]
    blogposts = BlogPost.objects.filter(project=project).order_by('-published')[:3]

    template = loader.get_template('wbcore/project.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'project': project,
        'event_item_list': item_list_from_occ(occurrences, text=False),
        'news': item_list_from_posts(news, host_slug=host_slug, post_type='news-post', id_key='post_id', text=False),
        'blogposts': item_list_from_posts(blogposts, host_slug=host_slug, post_type='blog-post', id_key='post_id', text=False),
        'host': host,
        'account': host.bank if host else None,
        'dot_nav': get_dot_nav(host=host),
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def hosts_view(request):
    hosts = Host.objects.all()

    template = loader.get_template('wbcore/hosts.html')
    context = {
        'hosts': hosts,
        'main_nav': get_main_nav(active='hosts'),
        'dot_nav': get_dot_nav(),
        'breadcrumb': [(_('Home'), reverse('home')), (_('Associations'), None)],
        'icon_links': icon_links
    }
    return HttpResponse(template.render(context, request))


def host_view(request, host_slug):
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None

        # replacing the link with the social media link # TODO no hardcoded links in general!
        for social_link in host.socialmedialink_set.all():
            icon_links[social_link.type]['link'] = social_link.link
    except Host.DoesNotExist:
        raise Http404()

    posts = NewsPost.objects.filter(host=host_slug).order_by('-published')[:5]
    posts = item_list_from_posts(posts, host_slug=host_slug)

    events = Event.objects.filter(host=host_slug).order_by('-start')[:3]
    period = Period(events, datetime.now(), datetime.now() + timedelta(365/2))
    try:
        welcome = Content.objects.get(host=host, type='welcome')
    except Content.DoesNotExist as e:
        welcome = None
    occurrences = period.get_occurrences()
    event_item_list = item_list_from_occ(occurrences, host_slug=host_slug)

    hosts = Host.objects.all()
    teams = Team.objects.filter(host=host)

    template = loader.get_template('wbcore/host.html')
    context = {
        'host': host,
        'breadcrumb': [(_('Home'), reverse('home')), (host.name, None)],
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'posts': posts,
        'hosts': hosts,
        'event_item_list': event_item_list,
        'teams': teams,
        'welcome': welcome,
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def events_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)
    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            events = Event.objects.filter(host__slug__in=host_slugs).distinct()
            breadcrumb = [(_('Home'), reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          (_('Events'), None)]
        except Host.DoesNotExist:
            raise Http404()
    else:
        host = None
        events = Event.objects.all()
        breadcrumb = [(_('Home'), reverse('home')), (_('Events'), None)]

    p = Period(events, datetime.now(), datetime.now() + timedelta(days=365))
    occurrences = p.get_occurrences()
    hosts = Host.objects.all()

    if Event.objects.count():
        latest = Event.objects.latest('start')
        erliest = Event.objects.earliest('start')
        start_date = erliest.start
        end_date = latest.start
        year_months = range_year_month(start_date, end_date)
    else:
        year_months = None

    if request.is_ajax():
        template = loader.get_template('wbcore/list_items.html')
    else:
        template = loader.get_template('wbcore/events.html')
    context = {
        'main_nav': get_main_nav(host=host, active='events'),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'hosts': hosts,
        'filter_preset': {'host': [host.slug] if host else None, },
        'from_to': year_months,
        'item_list': item_list_from_occ(occurrences, host_slug),
        'ajax_endpoint': reverse('ajax-filter-events'),
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def event_view(request, host_slug=None, event_slug=None):
    try:
        if host_slug:
            event = Event.objects.get(slug=event_slug, host__slug=host_slug)
            host = Host.objects.get(slug=host_slug)
            breadcrumb = [(_('Home'), reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          (_('Events'), reverse('events', args=[host_slug])),
                          (event.title, None)]
        else:
            event = Event.objects.get(slug=event_slug)
            host = None
            breadcrumb = [(_('Home'), reverse('home')), (_('Events'), reverse('events')), (event.title, None)]

    except Event.DoesNotExist:
        raise Http404()
    except Host.DoesNotExist:
        raise Http404()

    if event.form:
        form_instance = event.form
        form_class = form_instance.form()
        if request.method == 'POST':
            form = form_class(request.POST)
            if form.is_valid():
                form_instance.process(form, request)
                form = form_class()  # reset form
                form.success = True
        else:
            form = form_class()
    else:
        form = None

    event.image = event.get_title_image()

    if event.projects.exists():
        project_list = item_list_from_proj(event.projects.all(), host_slug=host_slug, text=False)[:3]
    else:
        projects = Project.objects.filter(hosts__slug=host_slug if host_slug else 'bundesverband')
        project_list = item_list_from_proj(projects, host_slug=host_slug)[:3]

    template = loader.get_template('wbcore/event.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'event': event,
        'project_item_list': project_list,
        'form': form,
        'breadcrumb': breadcrumb,
        'host': host,
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def blog_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)
    try:
        if host_slugs:
            posts = BlogPost.objects.filter(host__slug__in=host_slugs).distinct()
            host = Host.objects.get(slug=host_slug) if host_slug else None
        else:
            posts = BlogPost.objects.all()
            host = None
    except Host.DoesNotExist:
        raise Http404()

    posts = posts.order_by('-published')
    hosts = Host.objects.all()

    if BlogPost.objects.count():
        latest = BlogPost.objects.latest('published')
        earliest = BlogPost.objects.earliest('published')
        start_date = earliest.published
        end_date = latest.published

        year_months = range_year_month(start_date, end_date)
    else:
        year_months = None

    if host:
        breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Blog'), None)]
    else:
        breadcrumb = [(_('Home'), reverse('home')), (_('Blog'), None)]

    if request.is_ajax():
        template = loader.get_template('wbcore/list_items.html')
    else:
        template = loader.get_template('wbcore/blog.html')
    context = {
        'main_nav': get_main_nav(host=host, active='blog'),
        'dot_nav': get_dot_nav(host=host),
        'breadcrumb': breadcrumb,
        'host': host,
        'hosts': hosts,
        'filter_preset': {'host': [host.slug] if host else None, },
        'years': year_months,
        'item_list': item_list_from_posts(posts, host_slug, post_type="blog-post", id_key='post_id'),
        'ajax_endpoint': reverse('ajax-filter-blog'),
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def blog_post_view(request, host_slug=None, post_id=None):
    template = loader.get_template('wbcore/post.html')
    try:
        if host_slug:
            post = BlogPost.objects.get(pk=post_id, host__slug=host_slug)
            host = Host.objects.get(slug=host_slug)
            breadcrumb = [(_('Home'), reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          (_('Blog'), reverse('blog', args=[host_slug])),
                          (post.title, None)]
        else:
            post = BlogPost.objects.get(pk=post_id)
            host = None
            breadcrumb = [(_('Home'), reverse('home')), (_('Blog'), reverse('blog')), (post.title, None)]

    except BlogPost.DoesNotExist:
        raise Http404("The blog post does not exists!")
    except Host.DoesNotExist:
        raise Http404()

    if post.project:
        projects = item_list_from_proj([post.project], host_slug=host_slug)
    elif host:
        projects = item_list_from_proj(Project.objects.filter(hosts=host), host_slug=host_slug)
    else:
        projects = None

    post.type = "blog"

    context = {
        'main_nav': get_main_nav(host=host, active='blog'),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'post': post,
        'photos': post.photos,
        'projects': projects,
        'hosts': Host.objects.all(),
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def range_year_month(start_date, end_date):
    years = OrderedDict()
    d = date(year=start_date.year, month=start_date.month, day=1)
    end_date = date(year=end_date.year, month=end_date.month, day=1)
    months = []
    while d <= end_date:
        months.append(date(year=d.year, month=d.month, day=1))
        if d.month < 12:
            d = d.replace(month=d.month+1)
        else:
            years[d] = months
            d = d.replace(year=d.year+1, month=1, day=1)
            months = []
    if months:
        years[date(year=d.year, month=1, day=1)] = months
    return years


def news_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)
    try:
        if host_slugs:
            posts = NewsPost.objects.filter(host__slug__in=host_slugs).distinct()
            host = Host.objects.get(slug=host_slug) if host_slug else None
        else:
            posts = NewsPost.objects.all()
            host = None
    except Host.DoesNotExist:
        raise Http404()

    posts = item_list_from_posts(posts.order_by('-published'), host_slug=host_slug)
    hosts = Host.objects.all()

    if NewsPost.objects.count():
        latest = NewsPost.objects.latest('published')
        earliest = NewsPost.objects.earliest('published')
        start_date = earliest.published
        end_date = latest.published

        year_months = range_year_month(start_date, end_date)
    else:
        year_months = None

    if host:
        breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('News'), None)]
        for post in posts:
            post.current_host = host
    else:
        breadcrumb = [(_('Home'), reverse('home')), (_('News'), None)]

    if request.is_ajax():
        template = loader.get_template('wbcore/list_items.html')
    else:
        template = loader.get_template('wbcore/news.html')
    context = {
        'main_nav': get_main_nav(host=host, active='news'),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'posts': posts,
        'hosts': hosts,
        'filter_preset': {'host': [host.slug] if host else None, },
        'years': year_months,
        'item_list': posts,
        'icon_links': icon_links,
        'ajax_endpoint': reverse('ajax-filter-news'),
    }
    return HttpResponse(template.render(context, request))


def news_post_view(request, host_slug=None, post_id=None):
    template = loader.get_template('wbcore/post.html')
    try:
        if host_slug:
            post = NewsPost.objects.get(pk=post_id, host__slug=host_slug)
            host = Host.objects.get(slug=host_slug)
            breadcrumb = [(_('Home'), reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          (_('News'), reverse('news', args=[host_slug])),
                          (post.title, None)]
        else:
            post = NewsPost.objects.get(pk=post_id)
            host = None
            breadcrumb = [(_('Home'), reverse('home')), (_('News'), reverse('news')), (post.title, None)]

    except NewsPost.DoesNotExist:
        raise Http404("The post does not exists!")
    except Host.DoesNotExist:
        raise Http404()

    if post.project:
        projects = item_list_from_proj([post.project], host_slug=host_slug)
    elif host:
        projects = item_list_from_proj(Project.objects.filter(hosts=host), host_slug=host_slug)
    else:
        projects = None

    post.type = "news"

    context = {
        'main_nav': get_main_nav(host=host, active='news'),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'post': post,
        'photos': post.photos,
        'projects': projects,
        'hosts': Host.objects.all(),
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def host_projects_view(request, host_slug):
    template = loader.get_template('wbcore/projects.html')
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
    except Host.DoesNotExist:
        raise Http404()
    projects = Project.objects.filter(hosts__slug=host_slug)
    context = {
        'main_nav': get_main_nav(host=host, active='projects'),
        'dot_nav': get_dot_nav(host=host),
        'projects': projects,
        'host': host,
        'breadcrumb': [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Projects'), None)],
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def host_events_view(request, host_slug):
    template = loader.get_template('wbcore/events.html')
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
    except Host.DoesNotExist:
        raise Http404()
    events = Event.objects.filter(hosts__slug=host_slug)
    context = {
        'main_nav': get_main_nav(host=host, active='events'),
        'dot_nav': get_dot_nav(host=host),
        'events': events,
        'host': host,
        'breadcrumb': [(_('Home'), reverse('home')), (host.name, reverse('host', host_slug)), (_('Events'), None)],
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def search_view(request, query=None):
    template = loader.get_template('wbcore/search.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(),
        'breadcrumb': [(_('Home'), reverse('home')), (_('Search'), None)],
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def sitemap_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Sitemap'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Sitemap'), None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/sitemap.html')
    context = {
        'main_nav': get_main_nav(active='sitemap'),
        'dot_nav': get_dot_nav(host=host),
        'projects': projects,
        'host': host,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def donate_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Donate'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Donate'), None)]

    load_host = host if host else Host.objects.get(slug='bundesverband')
    account = load_host.bank
    try:
        donate = Content.objects.get(host=load_host, type='donate')
    except Content.DoesNotExist:
        donate = None

    projects = Project.objects.filter(hosts=host) if host else Project.objects.all()
    projects = projects[:3]

    template = loader.get_template('wbcore/donate.html')
    context = {
        'main_nav': get_main_nav(active='donate'),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'donate': donate,
        'account': account,
        'hosts': Host.objects.all(),
        'project_item_list': item_list_from_proj(projects, host_slug),
    }
    return HttpResponse(template.render(context, request))


def imprint_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Imprint'), None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('Imprint'), None)]

    teams = Team.objects.filter(host__slug='bundesverband')[:3]

    template = loader.get_template('wbcore/imprint.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'hosts': Host.objects.all(),
        'teams': item_list_from_teams(teams),
    }
    return HttpResponse(template.render(context, request))


def contact_view(request, host_slug=None):
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
    except Host.DoesNotExist:
        raise Http404()

    if host:
        breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('Contact'), None)]
    else:
        breadcrumb = [(_('Home'), reverse('home')), (_('Contact'), None)]

    load_host = host if host else Host.objects.get(slug='bundesverband')
    try:
        contact = Content.objects.get(host=load_host, type='contact')
    except Content.DoesNotExist:
        contact = None
    teams = Team.objects.filter(host=load_host)


    if teams:
        if len(teams) > 3:
            teams = teams[:3]
            more_teams = reverse('teams', args=[host_slug]) if host_slug else reverse('teams')
        else:
            more_teams = False
        teams = item_list_from_teams(teams, host_slug=host_slug)
    else:
        teams = False
        more_teams = False

    template = loader.get_template('wbcore/contact.html')
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': load_host,
        'breadcrumb': breadcrumb,
        'success': False,
        'icon_links': icon_links,
        'contact': contact,
        'teams': teams,
        'address': load_host.address,
        'more_teams': more_teams,
    }

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            email_template = loader.get_template('wbcore/contact_mail.html')
            contact_msg = form.save(commit=True)

            # sent info via email
            email = EmailMessage(
                to=[contact_msg.host.email],
                reply_to=[contact_msg.email],
                subject=contact_msg.subject,
                body=email_template.render(context={'msg': contact_msg}, request=request)
            )
            try:
               email.send()
               context['success'] = True
            # TODO handle error case more specifically
            except:
                # TODO render nice error page
                return HttpResponse('Message delivery failed.')
            return HttpResponse(template.render(context, request))
        else:
            context['success'] = False
    else:
        if host:
            form = ContactForm(initial={'host': host_slug})
        else:
            form = ContactForm()

    context['contact_form'] = form

    return HttpResponse(template.render(context, request))


def sitemap_view(request):
    template = loader.get_template('wbcore/sitemap.html')
    hosts = Host.objects.all()
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(),
        'hosts': hosts,
        'breadcrumb': [(_('Home'), reverse('home')), (_('Sitemap'), None)],
        'icon_links': icon_links,
    }
    return HttpResponse(template.render(context, request))


def faq_view(request, host_slug=None):
    if host_slug:
        try:
            host = Host.objects.get(slug=host_slug)
            breadcrumb = [(_('Home'), reverse('home')), (host.name, reverse('host', args=[host_slug])), (_('FAQ'), None)]
        except Host.DoesNotExist:
            raise Http404()
    else:
        host = None
        breadcrumb = [(_('Home'), reverse('home')), (_('FAQ'), None)]

    template = loader.get_template('wbcore/faq.html')
    faq = FAQ.objects.all()
    for f in faq:
        f.questionandanswer_set
    context = {
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'faq': faq,
        'breadcrumb': breadcrumb,
        'icon_links': icon_links,
        'hosts': Host.objects.all(),
    }
    return HttpResponse(template.render(context, request))

# TODO deprecated, should be removed in Jan 2021
def stadt_redirect(request, host_slug=None):
    '''redirects the host url from old homepage'''
    if host_slug:
        host_slug = host_slug.lower()  # typically old url was /Stadt/Münster
        host_slug = host_slug.replace('ä', 'ae')
        host_slug = host_slug.replace('ö', 'oe')
        host_slug = host_slug.replace('ü', 'ue')
        try:
            host = Host.objects.get(slug=host_slug)
        except Host.DoesNotExist:
            raise Http404()
    else:
        raise Http404()
    return HttpResponseRedirect("/%s" % host.slug)
