from django.urls import path
from django.conf.urls import include
from wbcore import rest_views
from wbcore import rest_url
from wbcore import views


main_patterns = [
    path('join/', views.join_view, name='join'),
    path('projects/', views.projects_view, name='projects'),
    path('projects/<str:project_slug>/', views.project_view, name='project'),
    path('events/', views.events_view, name='events'),
    path('events/<str:event_slug>/', views.event_view, name='event'),
    path('posts/<int:post_id>/', views.post_view, name='post'),
    path('posts/', views.posts_view, name='posts'),
]


urlpatterns = [
    path('', views.home_view, name='home'),
    path('rest/', include(rest_url.rest_patterns)),
    path('idea/', views.idea_view, name='idea'),
]

urlpatterns = urlpatterns + main_patterns

urlpatterns.append(path('<str:host_slug>/', include(main_patterns)))
urlpatterns.append(path('<str:host_slug>/', views.host_view, name='host'))

