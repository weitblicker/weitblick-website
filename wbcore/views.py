import csv
import os
import smtplib

from django.db.models import Count
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import reverse
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from datetime import timedelta, date
from wbcore.models import Host, Project, Event, NewsPost, Location, BlogPost, Team
from collections import OrderedDict
from .forms import ContactForm
from email.message import EmailMessage

EMAIL_ADDRESS = os.environ.get('TEST_EMAIL_USER')
EMAIL_PASSWORT = os.environ.get('TEST_EMAIL_PW')

dot_nav_news = NewsPost.objects.all().order_by('-published')[:3]
dot_nav_blog = BlogPost.objects.all().order_by('-published')[:3]
dot_nav_events = Event.objects.all().order_by('-start_date')[:3]

dot_nav = {'news': dot_nav_news,
           'blog': dot_nav_blog,
           'events': dot_nav_events}

icon_links = OrderedDict([
    ('login',
        {'name': 'Login',
         'link': 'https://new.weitblicker.org/admin',
         'icon': 'unlock alternate'}),
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
])


def get_main_nav(host=None, active=None):

    args = [host.slug] if host else []
    nav = OrderedDict([
            ('home', {'name': 'Home', 'link': reverse('home')}),
            ('idea', {'name': 'Idea', 'link': reverse('idea', args=args)}),
            ('projects', {'name': 'Projects', 'link': reverse('projects', args=args)}),
            ('events', {'name': 'Events', 'link': reverse('events', args=args)}),
            ('join', {'name': 'Join in', 'link': reverse('join', args=args)}),
            ('hosts', {'name': 'Unions', 'link': reverse('hosts')}),
    ])

    if active in nav:
        nav[active]['link'] = None

    return nav


def get_host_slugs(request, host_slug):
    if host_slug:
        host_slugs = [host_slug]
    else:
        host_slugs = request.GET.getlist("union")
        host_slugs = list(csv.reader(host_slugs))
        host_slugs = list(set().union(*host_slugs))
        host_slugs = [x.strip(' ') for x in host_slugs]
    return host_slugs


def home_view(request):
    projects = Project.objects.all()
    hosts = Host.objects.all()
    events = Event.objects.all().order_by('-start_date')[:3]
    posts = NewsPost.objects.all().order_by('-published')[:3]
    blog = BlogPost.objects.all().order_by('-published')[:3]

    template = loader.get_template('wbcore/home.html')

    context = {
        'main_nav': get_main_nav(),
        'dot_nav': dot_nav,
        'projects': projects,
        'hosts': hosts,
        'events': events,
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
        'dot_nav': dot_nav,
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
        'dot_nav': dot_nav,
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
        'dot_nav': dot_nav,
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
        'dot_nav': dot_nav,
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
        'dot_nav': dot_nav,
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
        'dot_nav': dot_nav,
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def team_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)

    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            breadcrumb = [('Team', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Team', None)]
        except:
            raise Http404()
    else:
        host = None
        breadcrumb = [('Home', reverse('home')), ('Team', None)]

    projects = Project.objects.all()

    template = loader.get_template('wbcore/team.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': dot_nav,
        'host': host,
        'breadcrumb': breadcrumb,
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
        'dot_nav': dot_nav,
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
        'main_nav': get_main_nav(active='idea'),
        'dot_nav': dot_nav,
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

    project_list = list(Location.objects.filter(project__in=projects).values(
            'country').annotate(number=Count('country')))
    context = {
        'main_nav': get_main_nav(host=host, active='projects'),
        'dot_nav': dot_nav,
        'projects': projects,
        'project_list': project_list,
        'breadcrumb': breadcrumb,
        'host': host,
    }
    template = loader.get_template('wbcore/projects.html')
    return HttpResponse(template.render(context, request))


def join_view(request, host_slug=None):
    template = loader.get_template('wbcore/join.html')
    context = {
        'main_nav': get_main_nav(active='join'),
        'dot_nav': dot_nav,
        'breadcrumb': [('Home', reverse('home')), ('Join in', None)],
    }
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
        'dot_nav': dot_nav,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def hosts_view(request):
    hosts = Host.objects.all()

    template = loader.get_template('wbcore/hosts.html')
    context = {
        'hosts': hosts,
        'main_nav': get_main_nav(active='hosts'),
        'dot_nav': dot_nav,
        'breadcrumb': [('Home', reverse('home')), ("Unions", None)],
    }
    return HttpResponse(template.render(context, request))



def host_view(request, host_slug):
    try:
        host = Host.objects.get(slug=host_slug)
    except Host.DoesNotExist:
        raise Http404()

    template = loader.get_template('wbcore/host.html')
    context = {
        'host': host,
        'breadcrumb': [('Home', reverse('home')), (host.name, None)],
        'main_nav': get_main_nav(host=host),
        'dot_nav': dot_nav,
    }
    return HttpResponse(template.render(context, request))


def events_view(request, host_slug=None):
    host_slugs = get_host_slugs(request, host_slug)
    if host_slugs:
        try:
            host = Host.objects.get(slug=host_slug) if host_slug else None
            events = Event.objects.filter(host__slug=host_slug)
            breadcrumb = [('Home', reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          ('Events', None)]
        except Host.DoesNotExist:
            raise Http404()
    else:
        host = None
        events = Event.objects.all()
        breadcrumb = [('Home', reverse('home')), ('Events', None)]

    template = loader.get_template('wbcore/events.html')
    context = {
        'main_nav': get_main_nav(host=host, active='events'),
        'dot_nav': dot_nav,
        'events': events,
        'host': host,
        'breadcrumb': breadcrumb,
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
                          (event.name, None)]
        else:
            event = Event.objects.get(slug=event_slug)
            host = None
            breadcrumb = [('Home', reverse('home')), ("Events", reverse('events')), (event.name, None)]

    except Event.DoesNotExist:
        raise Http404()
    except Host.DoesNotExist:
        raise Http404()

    template = loader.get_template('wbcore/events.html')
    context = {
        'main_nav': get_main_nav(host=host, active='events'),
        'dot_nav': dot_nav,
        'event': event,
        'breadcrumb': breadcrumb,
        'host': host
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

    if host:
        breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ("Blog", None)]
    else:
        breadcrumb = [('Home', reverse('home')), ('Blog', None)]

    context = {
        'main_nav': get_main_nav(host=host, active='blog'),
        'dot_nav': dot_nav,
        'posts': posts,
        'host': host,
        'breadcrumb': breadcrumb,
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
        'dot_nav': dot_nav,
        'post': post,
        'breadcrumb': breadcrumb,
        'host': host,
    }
    return HttpResponse(template.render(context, request))


def range_year_month(start_date, end_date):
    years = OrderedDict()
    d = date(year=start_date.year, month=start_date.month, day=1)
    end_date = date(year=end_date.year, month=end_date.month, day=1)
    print("End date:", end_date)
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
    template = loader.get_template('wbcore/news.html')

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
        print("Latest news:", end_date)
        print("Earliest news:", start_date)

        year_months = range_year_month(start_date, end_date)
        for year, months in year_months.items():
            print(year, months)
    else:
        year_months = None

    if host:
        breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ("News", None)]
    else:
        breadcrumb = [('Home', reverse('home')), ('News', None)]

    context = {
        'main_nav': get_main_nav(host=host, active='news'),
        'dot_nav': dot_nav,
        'posts': posts,
        'host': host,
        'hosts': hosts,
        'breadcrumb': breadcrumb,
        'years': year_months,
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
        'dot_nav': dot_nav,
        'post': post,
        'breadcrumb': breadcrumb,
        'host': host,
    }
    return HttpResponse(template.render(context, request))


def host_projects_view(request, host_slug):
    template = loader.get_template('wbcore/projects.html')
    host = Host.objects.get(slug=host_slug)
    projects = Project.objects.filter(hosts__slug=host_slug)
    context = {
        'main_nav': get_main_nav(host=host, active='projects'),
        'dot_nav': dot_nav,
        'projects': projects,
        'host': host,
        'breadcrumb': [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Projects', None)],
    }
    return HttpResponse(template.render(context, request))


def host_events_view(request, host_slug):
    template = loader.get_template('wbcore/events.html')
    host = Host.objects.get(slug=host_slug)
    events = Event.objects.filter(hosts__slug=host_slug)
    context = {
        'main_nav': get_main_nav(host=host, active='events'),
        'dot_nav': dot_nav,
        'events': events,
        'host': host,
        'breadcrumb': [('Home', reverse('home')), (host.name, reverse('host', host_slug)), ("Events", None)],
    }
    return HttpResponse(template.render(context, request))


def search_view(request, query=None):
    template = loader.get_template('wbcore/search.html')
    context = {
        'main_nav': get_main_nav(),
        'dot_nav': dot_nav,
        'breadcrumb': [('Home', reverse('home')), ("Search", None)],
    }
    return HttpResponse(template.render(context), request)


def contact_view(request, host_slug=None):
    try:
        host = Host.objects.get(slug=host_slug) if host_slug else None
    except Host.DoesNotExist:
        raise Http404()

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()

            # sent info via email
            msg = EmailMessage()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = 'admin@weitblicker.org'
            host = Host.objects.get(name=form.cleaned_data['host'])
            #msg['To'] = host.email
            msg['reply-to'] = form.cleaned_data['email']
            msg['Subject'] = form.cleaned_data['subject']
            msg.set_content('Name: ' + form.cleaned_data['name'] + "\n" + 'E-Mail: ' + form.cleaned_data['email'] + "\n\n" + "Nachricht: " + form.cleaned_data['message'])
            try:
                # TODO: optimize, ssl from the start (smtplib.SMTP_SSL) and/or django internal (django.core.mail.send_mail)
                with smtplib.SMTP('smtp.office365.com', 587) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORT)
                    smtp.send_message(msg)
            except BadHeaderError:
                print("error raised")
                return HttpResponse('Invalid header found.')
            # TODO: inform user on sucess
            messages.success(request, 'Message successfully sent. Thank you!')  # nowhere shown yet
            return redirect('home')
        else:
            message.error(request, 'Form not valid')
    else:
        if host:
            form = ContactForm(initial={'host': host_slug})
        else:
            form = ContactForm()

    if host:
        breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Contact', None)]
    else:
        breadcrumb = [('Home', reverse('home')), ('Contact', None)]

    template = loader.get_template('wbcore/contact.html')
    context = {
        'contact_form': form,
        'main_nav': get_main_nav(),
        'dot_nav': dot_nav,
        'host': host,
        'breadcrumb': breadcrumb,
    }

    return HttpResponse(template.render(context, request))


def sitemap_view(request):
    template = loader.get_template('wbcore/sitemap.html')
    hosts = Host.objects.all()
    teams = Team.objects.all()
    fixed = ['about', 'history', 'contact', 'join']

    context = {
        'main_nav': get_main_nav(),
        'dot_nav': dot_nav,
        'hosts': hosts,
        'teams': teams,
        'fixed': fixed,
        'breadcrumb': [('Home', reverse('home')), ("Sitemap", None)],
    }
    return HttpResponse(template.render(context), request)
