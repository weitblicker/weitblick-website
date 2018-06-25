from django.http import HttpResponse, JsonResponse
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
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
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
        'main_nav': [('Idea', None),
                     ('Projects', reverse('projects')),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
        'projects': projects,
        'hosts': hosts,
        'breadcrumb': [('Home', reverse('home')), ('Idea', None)],
    }
    return HttpResponse(template.render(context, request))


def projects_view(request):
    template = loader.get_template('wbcore/projects.html')
    projects = Project.objects.all()
    projects_countries_list = {"AF": 1,"IN": 2,"DZ": 5}
    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', None),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
        'projects': projects,
        'projects_countries_list': projects_countries_list,
        'breadcrumb': [('Home', reverse('home')), ('Projects', None)],
    }
    return HttpResponse(template.render(context, request))


def join_view(request):
    template = loader.get_template('wbcore/join.html')
    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', reverse('events')),
                     ('Join in', None)],
        'breadcrumb': [('Home', reverse('home')), ('Join in', None)],
    }
    return HttpResponse(template.render(context, request))


def project_view(request, project_slug):
    project = Project.objects.get(slug=project_slug)
    template = loader.get_template('wbcore/project.html')
    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', None),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
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
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', None),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
        'projects': projects,
        'host': host,
        'breadcrumb': [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ('Projects', None)],
    }
    return HttpResponse(template.render(context, request))


def events_view(request):
    events = Event.objects.all()
    #some examples to get markers on the map
    cities = {'HD':{
            "name": 'Heidelberg', "latLng": [49.3987524,8.672433500000011]},
          'Mu':{"name": 'Münster', "latLng": [51.9606649,7.626134699999966]}}
    template = loader.get_template('wbcore/events.html')
    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', None),
                     ('Join in', reverse('join'))],
        'city_list': cities,
        'events': events,
        'breadcrumb': [('Home', reverse('home')), ('Events', None)],
    }
    return HttpResponse(template.render(context, request))


def host_events_view(request, host_slug):
    template = loader.get_template('wbcore/events.html')
    host = Host.objects.get(slug=host_slug)
    events = Event.objects.filter(hosts__slug=host_slug)
    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', None),
                     ('Join in', reverse('join'))],
        'events': events,
        'host': host,
        'breadcrumb': [('Home', reverse('home')), (host.name, reverse('host', host_slug)), ("Events", None)],
    }
    return HttpResponse(template.render(context, request))


def event_view(request, event_slug):
    template = loader.get_template('wbcore/events.html')
    event = Event.objects.get(slug=event_slug)
    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', None),
                     ('Join in', reverse('join'))],
        'event': event,
        'breadcrumb': [('Home', reverse('home')), ("Events", reverse('events')), (event.name, None)],
    }
    return HttpResponse(template.render(context, request))


def search_view(request):
    if request.method == "POST":
        search_text = request.POST['search_text']
        search_type = request.POST['search_type']
    else:
        search_text = ''
        search_text = ''

    return JsonResponse()

