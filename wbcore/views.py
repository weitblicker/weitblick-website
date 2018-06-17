from django.http import HttpResponse
from django.template import loader
from django.urls import reverse
from .models import Host, Project, Event, Post

def home_view(request):
    projects = Project.objects.all()
    hosts = Host.objects.all()
    events = Event.objects.all()
    posts = Post.objects.all()

    template = loader.get_template('wbcore/home.html')
    context = {
        'projects': projects,
        'hosts': hosts,
        'events': events,
        'posts': posts,
        'breadcrumb': [('Home', None)],
    }
    return HttpResponse(template.render(context, request))


def idea_view(request):
    projects = Project.objects.all()
    hosts = Project.objects.all()

    template = loader.get_template('wbcore/idea.html')
    context = {
        'projects': projects,
        'hosts': hosts,
        'breadcrumb': [('Home', reverse('home')), ('Idea', None)],
    }
    return HttpResponse(template.render(context, request))


def projects_view(request):
    template = loader.get_template('wbcore/projects.html')
    projects = Project.objects.all()
    context = {
        'projects': projects,
        'breadcrumb': [('Home', reverse('home')), ('Projects', None)],
    }
    return HttpResponse(template.render(context, request))


def join_view(request):
    template = loader.get_template('wbcore/join.html')
    context = {
        'breadcrumb': [('Home', reverse('home')), ('Join in', None)],
    }
    return HttpResponse(template.render(context, request))


def project_view(request, project_slug):
    project = Project.objects.get(slug=project_slug)
    template = loader.get_template('wbcore/project.html')
    context = {
        'project': project,
        'breadcrumb': [('Home', reverse('home')), ('Projects', reverse('projects')), (project.name, None)],
    }
    return HttpResponse(template.render(context, request))


def host_view(request, host_slug):
    host = Host.objects.get(slug=host_slug)
    template = loader.get_template('wbcore/host.html')
    context = {
        'host': host,
        'breadcrumb': [('Home', reverse('home')), (host.name, None)],
    }
    return HttpResponse(template.render(context, request))


def host_projects_view(request, host_slug):
    template = loader.get_template('wbcore/projects.html')
    host = Host.objects.get(slug=host_slug)
    projects = Project.objects.filter(hosts__slug=host_slug)
    context = {
        'projects': projects,
        'host': host,
        'breadcrumb': [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Projects', None)],
    }
    return HttpResponse(template.render(context, request))


def events_view(request):
    events = Event.objects.all()
    template = loader.get_template('wbcore/events.html')
    context = {
        'events': events,
        'breadcrumb': [('Home', reverse('home')), ('Events', None)],
    }
    return HttpResponse(template.render(context, request))


def host_events_view(request, host_slug):
    template = loader.get_template('wbcore/events.html')
    host = Host.objects.get(slug=host_slug)
    events = Event.objects.filter(hosts__slug=host_slug)
    context = {
        'events': events,
        'host': host,
        'breadcrumb': [('Home', reverse('home')), (host.name, reverse('host', host_slug)), ("Events", None)],
    }
    return HttpResponse(template.render(context, request))


def event_view(request, event_slug):
    template = loader.get_template('wbcore/events.html')
    event = Event.objects.get(slug=event_slug)
    context = {
        'event': event,
        'breadcrumb': [('Home', reverse('home')), ("Events", reverse('events')), (event.name, None)],
    }
    return HttpResponse(template.render(context, request))


