from django.urls import path
from wbcore import ajax_views

ajax_patterns = [
    path('filter-news/', ajax_views.filter_news_view, name='ajax-filter-news'),
    path('filter-projects/', ajax_views.filter_projects_view, name='ajax-filter-projects'),
    path('filter-events/', ajax_views.filter_events_view, name='ajax-filter-events'),
    path('filter-blog/', ajax_views.filter_blog_view, name='ajax-filter-blog'),
    path('search/<str:query>/', ajax_views.search, name='ajax-search'),
]
