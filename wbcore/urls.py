from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('idea/', views.idea_view, name='idea'),
    path('projects/', views.projects_view, name='projects'),
    path('projects/<str:project_slug>/', views.project_view, name='project'),
    path('events/', views.events_view, name='events'),
    path('events/<str:event_slug>/', views.event_view, name='event'),
    path('join/', views.join_view, name='join'),
    path('<str:host_slug>/', views.host_view, name='host'),
    path('<str:host_slug>/projects/', views.host_projects_view, name='host_projects'),
    path('<str:host_slug>/events/', views.host_events_view, name='host_events'),
]