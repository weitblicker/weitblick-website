import csv

from django.db.models import Count
from django.http import HttpResponse, Http404
from django.template import loader
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

from wbcore.tokens import account_activation_token

from wbcore.forms import (
    ContactForm, UserForm, BankForm, UserRelationForm, AddressForm, User)

from wbcore.models import (
    Host, Project, Event, NewsPost, Location, BlogPost, Team, TeamUserRelation, UserRelation, JoinPage)


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
         'link': 'https://www.instagram.com/weitblick_osnabrueck/',
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
                    'name': 'Home',
                    'link': reverse('home'),
                    'icon': 'wbcore/svgs/home.svg',
                    'mobile': False,
                }),
            ('idea',
                {
                    'name': 'Idee',
                    'link': reverse('idea', args=args),
                    'icon': 'wbcore/svgs/idea.svg',
                    'mobile': True,
                }),
            ('projects',
                {
                    'name': 'Projekte',
                    'link': reverse('projects', args=args),
                    'icon': 'wbcore/svgs/leaf.svg',
                    'mobile': True,
                }),
            ('events',
                {
                    'name': 'Events',
                    'link': reverse('events', args=args),
                    'icon': 'wbcore/svgs/hand.svg',
                    'mobile': True,
                }),
            ('join',
                {
                    'name': 'Mitmachen',
                    'link': reverse('join', args=args),
                    'icon': 'wbcore/svgs/people.svg',
                    'mobile': True,
                }),
            ('hosts',
                {
                    'name': 'Vereine',
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
        events = Event.objects.filter(host=host)
        occurences =  Period(events, datetime.now(), datetime.now() + timedelta(days=365)).get_occurrences()[:3]
    else:
        news = NewsPost.objects.all().order_by('-published')[:3]
        blog = BlogPost.objects.all().order_by('-published')[:3]
        events =  Event.objects.all()#.order_by('-start')[:3]
        occurences = Period(events, datetime.now(), datetime.now() + timedelta(days=365)).get_occurrences()[:3]
    return {'news': news, 'blog': blog, 'events': occurences}


def get_host_slugs(request, host_slug):
    if host_slug:
        host_slugs = [host_slug]
    else:
        host_slugs = request.GET.getlist("union")
        host_slugs = list(csv.reader(host_slugs))
        host_slugs = list(set().union(*host_slugs))
        host_slugs = [x.strip(' ') for x in host_slugs]
    return host_slugs


def item_list_from_occ(occurrences, host_slug=None):
    # set attributes to fill list_item template
    item_list = []
    for occ in occurrences:
        occ.image = occ.event.image
        # occ.date = occ.start
        occ.show_date = f"{occ.start.strftime('%a, %d. %b %Y')} - {occ.end.strftime('%a, %d. %b %Y')}"
        occ.hosts = occ.event.host.all()
        current_host = Host.objects.get(slug=host_slug) if host_slug else None
        if current_host and current_host in occ.event.host.all():
            occ.link = reverse('event', kwargs={'event_slug': occ.event.slug, 'host_slug': host_slug})
        else:
            occ.link = reverse('event', args=[occ.event.slug])
        occ.teaser = occ.description
        item_list.append(occ)
    return item_list


def item_list_from_blogposts(blogposts, host_slug=None):
    item_list = []
    for post in blogposts:
        if not post.teaser:
            post.teaser = post.text
        current_host = Host.objects.get(slug=host_slug) if host_slug else None
        if current_host and post.host and current_host in post.host.all():
            post.link = reverse('blog-post', kwargs={'post_id': post.id, 'host_slug': host_slug})
        else:
            post.link = reverse('blog-post', args=[post.id])
        item_list.append(post)
    return item_list


def item_list_from_proj(projects, host_slug=None):
    item_list = []
    for project in projects:
        project.image = project.teaser_image()
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
        #project.teaser = project.description
        item_list.append(project)
    return item_list


def home_view(request):
    projects = Project.objects.all()
    hosts = Host.objects.all()
    posts = NewsPost.objects.all().order_by('-published')[:3]
    blog = BlogPost.objects.all().order_by('-published')[:3]
    events = Event.objects.all().order_by('-start')
    period = Period(events, datetime.now(), datetime.now() + timedelta(365/2))
    occurrences = period.get_occurrences()[:3]

    template = loader.get_template('wbcore/home.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(),
        'projects': projects,
        'hosts': hosts,
        'occurrences': occurrences,
        'posts': posts,
        'breadcrumb': [('Home', None)],
        'icon_links': icon_links
    }
    return HttpResponse(template.render(context, request))


def reports_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Reports', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Reports', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Reports', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/reports.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def charter_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Charter', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Charter', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Charter', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/charter.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def transparency_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Transparency', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Transparency', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Transparency', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/transparency.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def facts_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Facts', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Facts', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Facts', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/facts.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def history_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('History', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('History', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('History', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/history.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def privacy_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Privacy', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Privacy', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Privacy', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/privacy.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def teams_view(request, host_slug=None):
    try:
        if not host_slug:
            host = Host.objects.get(slug='bundesverband')
        else:
            host = Host.objects.get(slug=host_slug)
    except Host.DoesNotExist:
        raise Http404()
    if host:
        try:
            breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Team', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Team', None)]

    teams = Team.objects.filter(host=host)

    template = loader.get_template('wbcore/teams.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'teams': teams
    }
    return HttpResponse(template.render(context, request))


def team_view(request, host_slug=None, team_slug=None):
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
    except Host.DoesNotExist:
        raise Http404()

    try:
        team = Team.objects.get(slug=team_slug, host=host)
    except Team.DoesNotExist:
        raise Http404()

    if not team:    # TODO check if this is reachable, I think this is useless here.
        raise Http404()

    if host:
        try:
            breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Team', reverse('teams')), (team.name, None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Team', reverse('teams')), (team.name, None)]

    members = team.member.all()
    relations = []
    for member in members:
        relations.append(TeamUserRelation.objects.get(user=member))

    members_relations = sorted(zip(members, relations), key=lambda tup: (tup[1].priority, tup[0].name.split(" ")[-1]))

    template = loader.get_template('wbcore/team.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'team': team,
        'members_relations': members_relations,
    }
    return HttpResponse(template.render(context, request))


def about_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('About', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('About', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/about.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def idea_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)
    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Idea', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Idea', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/idea.html')
    context = {
        'main_nav': get_main_nav(active='idea', host=host),
        'dot_nav': get_dot_nav(host=host),
        'projects': projects,
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def projects_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            projects = Project.objects.filter(hosts__slug__in=host_slugs).distinct()
            breadcrumb = [('Home', reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          ('Projects', None)]
        except Host.DoesNotExist:
            raise Http404()
    else:
        host = None
        projects = Project.objects.all()
        breadcrumb = [('Home', reverse('home')), ('Projects', None)]
    posts = BlogPost.objects.filter(project__in=projects)

    countries = set([project.location.country for project in projects])

    project_list = list(Location.objects.filter(project__in=projects).values(
            'country').annotate(number=Count('country')))

    hosts = Host.objects.all()

    template = loader.get_template('wbcore/projects.html')
    context = {
        'main_nav': get_main_nav(host=host, active='projects'),
        'dot_nav': get_dot_nav(host=host),
        'breadcrumb': breadcrumb,
        'item_list': item_list_from_proj(projects, host_slug),
        'project_list': project_list,
        'host': host,
        'hosts': hosts,
        'posts': posts,
        'countries': countries,
        'filter_visibility': True,
        'ajax_endpoint': reverse('ajax-filter-projects'),
    }
    return HttpResponse(template.render(context, request))


def signup(user, host):
    subject = 'Mitgliedsantrag ' + host.name
    message = loader.render_to_string('wbcore/activation_email.html', {
        'domain': Site.objects.get_current().domain,
        'user': user,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
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
        breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Contact', None)]
        submit_url = reverse('join', args=[host_slug])
        try:
            join_page = host.joinpage
            print("Join Page", join_page)
        except JoinPage.DoesNotExist:
            pass
    else:
        submit_url = reverse('join')
        breadcrumb = [('Home', reverse('home')), ('Contact', None)]

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

    context = {
        'main_nav': get_main_nav(active='join'),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': [('Home', reverse('home')), ('Join in', None)],
        'success': success,
    }

    if join_page:
        print("TestTestTest")
        context['image'] = join_page.image
        context['sepa_text'] = join_page.sepa_text
        context['text'] = join_page.text
        context['user_form'] = user_form
        context['bank_form'] = bank_form
        context['urel_form'] = urel_form
        context['addr_form'] = addr_form
        context['submit_url'] = submit_url
        context['enable_form'] = join_page.enable_form

    return HttpResponse(template.render(context, request))


def project_view(request, host_slug=None, project_slug=None):

    try:
        if host_slug:
            project = Project.objects.get(slug=project_slug, hosts__slug=host_slug)
            host = Host.objects.get(host_slug=host_slug)
            breadcrumb = [('Home', reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          ('Projects', reverse('projects')),
                          (project.name, None)]
        else:
            project = Project.objects.get(slug=project_slug)
            host = None
            breadcrumb = [('Home', reverse('home')), ('Projects', reverse('projects')), (project.name, None)]
    except Project.DoesNotExist:
        raise Http404("Project does not exist!")
    except Host.DoesNotExist:
        raise Http404("Host does not exist!")

    template = loader.get_template('wbcore/project.html')
    context = {
        'main_nav': get_main_nav(host=host, active='projects'),
        'project': project,
        'host': host,
        'dot_nav': get_dot_nav(host=host),
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def hosts_view(request):
    hosts = Host.objects.all()

    template = loader.get_template('wbcore/hosts.html')
    context = {
        'hosts': hosts,
        'main_nav': get_main_nav(active='hosts'),
        'dot_nav': get_dot_nav(),
        'breadcrumb': [('Home', reverse('home')), ("Unions", None)],
    }
    return HttpResponse(template.render(context, request))


def host_view(request, host_slug):
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
    except Host.DoesNotExist:
        raise Http404()

    posts = NewsPost.objects.filter(host=host_slug).order_by('-published')[:5]
    events = Event.objects.filter(host=host_slug).order_by('-start')[:3]
    period = Period(events, datetime.now(), datetime.now() + timedelta(365/2))
    occurrences = period.get_occurrences()
    hosts = Host.objects.all()
    teams = Team.objects.filter(host=host)

    template = loader.get_template('wbcore/host.html')
    context = {
        'host': host,
        'hosts': hosts,
        'breadcrumb': [('Home', reverse('home')), (host.name, None)],
        'main_nav': get_main_nav(host=host),
        'dot_nav': get_dot_nav(host=host),
        'posts': posts,
        'occurrences': occurrences,
        'teams': teams
    }
    return HttpResponse(template.render(context, request))


def events_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)
    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            events = Event.objects.filter(host__slug__in=host_slugs).distinct()
            breadcrumb = [('Home', reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          ('Events', None)]
        except Host.DoesNotExist:
            raise Http404()
    else:
        host = None
        events = Event.objects.all()
        breadcrumb = [('Home', reverse('home')), ('Events', None)]

    p = Period(events, datetime.now(), datetime.now() + timedelta(days=365/2))
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

    template = loader.get_template('wbcore/events.html')
    context = {
        'main_nav': get_main_nav(host=host, active='events'),
        'dot_nav': get_dot_nav(host=host),
        'breadcrumb': breadcrumb,
        'hosts': hosts,
        'from_to': year_months,
        'item_list': item_list_from_occ(occurrences, host_slug),
        'ajax_endpoint': reverse('ajax-filter-events'),
    }
    return HttpResponse(template.render(context, request))


def event_view(request, host_slug=None, event_slug=None):
    try:
        if host_slug:
            event = Event.objects.get(slug=event_slug, host__slug=host_slug)
            host = Host.objects.get(slug=host_slug)
            breadcrumb = [('Home', reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          ("Events", reverse('events', args=[host_slug])),
                          (event.title, None)]
        else:
            event = Event.objects.get(slug=event_slug)
            host = None
            breadcrumb = [('Home', reverse('home')), ("Events", reverse('events')), (event.title, None)]

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

    template = loader.get_template('wbcore/event.html')
    context = {
        'main_nav': get_main_nav(host=host, active='events'),
        'dot_nav': get_dot_nav(host=host),
        'event': event,
        'form': form,
        'breadcrumb': breadcrumb,
        'host': host,
    }
    return HttpResponse(template.render(context, request))


def blog_view(request, host_slug=None):
    template = loader.get_template('wbcore/blog.html')

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

    posts = posts.order_by('-published')[:20]
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
        breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ("Blog", None)]
    else:
        breadcrumb = [('Home', reverse('home')), ('Blog', None)]

    context = {
        'main_nav': get_main_nav(host=host, active='blog'),
        'dot_nav': get_dot_nav(host=host),
        'breadcrumb': breadcrumb,
        'host': host,
        'hosts': hosts,
        'years': year_months,
        'item_list': item_list_from_blogposts(posts, host_slug),
        'ajax_endpoint': reverse('ajax-filter-blog'),
    }
    return HttpResponse(template.render(context, request))


def blog_post_view(request, host_slug=None, post_id=None):
    template = loader.get_template('wbcore/blog_post.html')
    try:
        if host_slug:
            post = BlogPost.objects.get(pk=post_id, host__slug=host_slug)
            host = Host.objects.get(slug=host_slug)
            breadcrumb = [('Home', reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          ('Blog', reverse('blog', args=[host_slug])),
                          (post.title, None)]
        else:
            post = BlogPost.objects.get(pk=post_id)
            host = None
            breadcrumb = [('Home', reverse('home')), ("Blog", reverse('blog')), (post.title, None)]

    except BlogPost.DoesNotExist:
        raise Http404("The blog post does not exists!")
    except Host.DoesNotExist:
        raise Http404()

    context = {
        'main_nav': get_main_nav(host=host, active='blog'),
        'dot_nav': get_dot_nav(host=host),
        'post': post,
        'breadcrumb': breadcrumb,
        'host': host,
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

    posts = posts.order_by('-published')[:20]
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
        breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ("News", None)]
        for post in posts:
            post.current_host = host
    else:
        breadcrumb = [('Home', reverse('home')), ('News', None)]

    template = loader.get_template('wbcore/news.html')
    context = {
        'main_nav': get_main_nav(host=host, active='news'),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'posts': posts,
        'hosts': hosts,
        'years': year_months,
        'item_list': posts,
        'ajax_endpoint': reverse('ajax-filter-news'),
    }
    return HttpResponse(template.render(context, request))


def news_post_view(request, host_slug=None, post_id=None):
    template = loader.get_template('wbcore/news_post.html')
    try:
        if host_slug:
            post = NewsPost.objects.get(pk=post_id, host__slug=host_slug)
            host = Host.objects.get(slug=host_slug)
            breadcrumb = [('Home', reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          ('News', reverse('news', args=[host_slug])),
                          (post.title, None)]
        else:
            post = NewsPost.objects.get(pk=post_id)
            host = None
            breadcrumb = [('Home', reverse('home')), ("News", reverse('news')), (post.title, None)]

    except NewsPost.DoesNotExist:
        raise Http404("The post does not exists!")
    except Host.DoesNotExist:
        raise Http404()

    context = {
        'main_nav': get_main_nav(host=host, active='news'),
        'dot_nav': get_dot_nav(host=host),
        'post': post,
        'breadcrumb': breadcrumb,
        'host': host,
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
        'breadcrumb': [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Projects', None)],
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
        'breadcrumb': [('Home', reverse('home')), (host.name, reverse('host', host_slug)), ("Events", None)],
    }
    return HttpResponse(template.render(context, request))


def search_view(request, query=None):
    template = loader.get_template('wbcore/search.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(),
        'breadcrumb': [('Home', reverse('home')), ("Search", None)],
    }
    return HttpResponse(template.render(context), request)


def sitemap_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Sitemap', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Sitemap', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/sitemap.html')
    context = {
        'main_nav': get_main_nav(active='sitemap'),
        'dot_nav': get_dot_nav(host=host),
        'projects': projects,
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def donate_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('donate', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('donate', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/donate.html')
    context = {
        'main_nav': get_main_nav(active='donate'),
        'dot_nav': get_dot_nav(host=host),
        'projects': projects,
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def imprint_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Imprint', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Imprint', None)]

    template = loader.get_template('wbcore/imprint.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def contact_view(request, host_slug=None):
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
    except Host.DoesNotExist:
        raise Http404()

    if host:
        breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Contact', None)]
    else:
        breadcrumb = [('Home', reverse('home')), ('Contact', None)]

    template = loader.get_template('wbcore/contact.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': get_dot_nav(host=host),
        'host': host,
        'breadcrumb': breadcrumb,
        'success': False,
    }

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()

            # sent info via email
            name = form.cleaned_data['name']
            email_addr = form.cleaned_data['email']
            msg = form.cleaned_data['message']

            # TODO use template for this
            message = 'Name: ' + name + '\n'
            message += 'E-Mail: ' + email_addr + '\n\n'
            message += 'Nachricht: ' + msg

            email = EmailMessage(
                to=['admin@weitblicker.org'],
                reply_to=[form.cleaned_data['email']],
                subject=form.cleaned_data['email'],
                body=message
            )
            try:
               email.send()
               context['success'] = True
            # TODO handle error case more specifically
            except:
                return HttpResponse('Invalid header found.')
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
        'breadcrumb': [('Home', reverse('home')), ("Sitemap", None)],
    }
    return HttpResponse(template.render(context), request)
