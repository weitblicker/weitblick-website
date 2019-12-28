from django.urls import path, re_path
from django.conf.urls import include
from django.contrib.sitemaps.views import sitemap
from .sitemaps import NewsPostSitemap, ProjectSitemap, BlogPostSitemap, EventSitemap, TeamSitemap, HostSitemap
from .sitemaps import AboutSitemap, HistorySitemap, ContactSitemap, JoinSitemap
from wbcore import views, rest_views, ajax_views
from wbcore import rest_urls, ajax_urls

sitemaps = {
    'news': NewsPostSitemap,
    'project': ProjectSitemap,
    'blogpost': BlogPostSitemap,
    'event': EventSitemap,
    'team': TeamSitemap,
    'host': HostSitemap,
    'about': AboutSitemap,
    'history': HistorySitemap,
    'contact': ContactSitemap,
    'join': JoinSitemap,
}

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
    path('about/', views.about_view, name='about'),
    path('history/', views.history_view, name='history'),
    path('team/<str:team_slug>/', views.team_view, name='team'),
    path('team/', views.teams_view, name='teams'),
    path('contact/', views.contact_view, name='contact'),
    path('transparency/', views.transparency_view, name='transparency'),
    path('charter/', views.charter_view, name='charter'),
    path('reports/', views.reports_view, name='reports'),
    path('facts/', views.facts_view, name='facts'),
    path('donate/', views.donate_view, name='donate'),
    path('privacy/', views.privacy_view, name="privacy"),
    path('imprint/', views.imprint_view, name='imprint'),
]

urlpatterns = [
    path('', views.home_view, name='home'),
    path('rest/', include(rest_urls.rest_patterns)),
    path('ajax/', include(ajax_urls.ajax_patterns)),
    path('faq/', views.faq_view, name='faq'),
    path('union/', views.hosts_view, name='hosts'),
    path('search/', views.search_view, name='search'),
    path('sitemap/', views.sitemap_view, name='sitemap'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('search/<str:query>/', views.search_view, name='search'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            views.activate_user, name='activate'),
    # path('search/', include('haystack.urls')),
]

urlpatterns = urlpatterns + main_patterns

urlpatterns.append(path('<str:host_slug>/', include(main_patterns)))
urlpatterns.append(path('<str:host_slug>/', views.host_view, name='host'))
