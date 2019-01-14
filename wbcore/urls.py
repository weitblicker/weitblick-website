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
    path('news/<int:post_id>/', views.news_post_view, name='news-post'),
    path('news/', views.news_view, name='news'),
    path('blog/<int:post_id>/', views.blog_post_view, name='blog-post'),
    path('blog/', views.blog_view, name='blog'),
    path('idea/', views.idea_view, name='idea'),
]


urlpatterns = [
    path('', views.home_view, name='home'),
    path('rest/', include(rest_url.rest_patterns)),
    path('search/<str:query>/', rest_views.search),
    path('union/', views.hosts_view, name='hosts'),
    #path('search/', include('haystack.urls')),
]

urlpatterns = urlpatterns + main_patterns

urlpatterns.append(path('<str:host_slug>/', include(main_patterns)))
urlpatterns.append(path('<str:host_slug>/', views.host_view, name='host'))

