from django.http import HttpResponse, JsonResponse, Http404
from django.template import loader
from django.urls import reverse
from .models import Host, Project, Event, Post, BlogPost
from num2words import num2words
import csv

more_nav = [{'title': 'Gruppe A', 'links': [('Item A.1', '#'), ('Item A.2', '#')]},
            {'title': 'Gruppe B', 'links': [('Item B.1', '#'), ('Item B.2', '#')]},
            {'title': 'Gruppe B', 'links': [('Item B.1', '#'), ('Item B.2', '#')]},
            {'title': 'Gruppe B', 'links': [('Item B.1', '#'), ('Item B.2', '#')]},
            {'title': 'Gruppe B', 'links': [('Item B.1', '#'), ('Item B.2', '#')]},
            {'title': 'Gruppe C', 'links': [('Item C.1', '#'), ('Item C.2', '#'), ('Item C.3', '#')]}]


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
    events = Event.objects.all()
    posts = Post.objects.all()

    template = loader.get_template('wbcore/home.html')

    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
        'more_nav': (more_nav, num2words(len(more_nav))),
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
        'more_nav': (more_nav, num2words(len(more_nav))),
        'projects': projects,
        'hosts': hosts,
        'breadcrumb': [('Home', reverse('home')), ('Idea', None)],
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


    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', None),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
        'more_nav': (more_nav, num2words(len(more_nav))),
        'projects': projects,
        'breadcrumb': breadcrumb,
    }
    template = loader.get_template('wbcore/projects.html')
    return HttpResponse(template.render(context, request))


def join_view(request, host_slug=None):
    template = loader.get_template('wbcore/join.html')
    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', reverse('events')),
                     ('Join in', None)],
        'more_nav': (more_nav, num2words(len(more_nav))),
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
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', None),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
        'project': project,
        'host': host,
        'more_nav': (more_nav, num2words(len(more_nav))),
        'breadcrumb': breadcrumb,
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
        breadcrumb = [('Home', reverse('home')), ('Events', None)],

    template = loader.get_template('wbcore/events.html')
    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', None),
                     ('Join in', reverse('join'))],
        'more_nav': (more_nav, num2words(len(more_nav))),
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
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', None),
                     ('Join in', reverse('join'))],
        'more_nav': (more_nav, num2words(len(more_nav))),
        'event': event,
        'breadcrumb': breadcrumb,
        'host': host
    }
    return HttpResponse(template.render(context, request))


def post_view(request, host_slug=None, post_id=None):
    template = loader.get_template('wbcore/post.html')
    try:
        if host_slug:
            post = Post.objects.get(pk=post_id, host__slug=host_slug)
            host = Host.objects.get(slug=host_slug)
            breadcrumb = [('Home', reverse('home')),
                          (host.name, reverse('host', args=[host_slug])),
                          ('Posts', reverse('posts', args=[host_slug])),
                          (post.title, None)]
        else:
            post = Post.objects.get(pk=post_id)
            host = None
            breadcrumb = [('Home', reverse('home')), ("Posts", reverse('posts')), (post.title, None)]

    except Post.DoesNotExist:
        raise Http404("The post does not exists!")
    except Host.DoesNotExist:
        raise Http404()

    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
        'more_nav': (more_nav, num2words(len(more_nav))),
        'post': post,
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

    posts = posts.order_by('-published')
    posts = reversed(posts)

    if host:
        breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ("Blog", None)]
    else:
        breadcrumb = [('Home', reverse('home')), ('Blog', None)]

    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', None),
                     ('Join in', reverse('join'))],
        'more_nav': (more_nav, num2words(len(more_nav))),
        'posts': posts,
        'host': host,
        'breadcrumb': breadcrumb,
    }
    return HttpResponse(template.render(context, request))


def blog_post_view(request, host_slug=None, post_id=None):
    template = loader.get_template('wbcore/post.html')
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
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', reverse('events')),
                     ('Join in', reverse('join'))],
        'more_nav': (more_nav, num2words(len(more_nav))),
        'post': post,
        'breadcrumb': breadcrumb,
        'host': host,
    }
    return HttpResponse(template.render(context, request))


def posts_view(request, host_slug=None):
    template = loader.get_template('wbcore/posts.html')

    host_slugs = get_host_slugs(request, host_slug)
    try:
        if host_slugs:
            posts = Post.objects.filter(host__slug__in=host_slugs).distinct()
            host = Host.objects.get(slug=host_slug) if host_slug else None
        else:
            posts = Post.objects.all()
            host = None
    except Host.DoesNotExist:
        raise Http404()

    posts = posts.order_by('-published')
    posts = reversed(posts)

    if host:
        breadcrumb = [('Home', reverse('home')), (host.name, reverse('host', args=[host_slug])), ("Posts", None)]
    else:
        breadcrumb = [('Home', reverse('home')), ('Post', None)]

    context = {
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', None),
                     ('Join in', reverse('join'))],
        'more_nav': (more_nav, num2words(len(more_nav))),
        'posts': posts,
        'host': host,
        'breadcrumb': breadcrumb,
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
        'more_nav': (more_nav, num2words(len(more_nav))),
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
        'main_nav': [('Idea', reverse('idea')),
                     ('Projects', reverse('projects')),
                     ('Events', None),
                     ('Join in', reverse('join'))],
        'more_nav': (more_nav, num2words(len(more_nav))),
        'events': events,
        'host': host,
        'breadcrumb': [('Home', reverse('home')), (host.name, reverse('host', host_slug)), ("Events", None)],
    }
    return HttpResponse(template.render(context, request))


def search_view(request, query):
    if request.method == "POST":
        search_text = request.POST['search_text']
        search_type = request.POST['search_type']
    else:
        search_text = ''
        search_text = ''

    return JsonResponse()

