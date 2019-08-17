from django.urls import path
from wbcore import ajax_views

ajax_patterns = [
    path('filter-news/', ajax_views.filter_news, name='ajax-filter-news'),
    path('filter-projects/', ajax_views.filter_projects, name='ajax-filter-projects'),
    path('filter-events/', ajax_views.filter_events, name='ajax-filter-events'),
    path('filter-blog/', ajax_views.filter_blog, name='ajax-filter-blog'),
    path('search/<str:query>/', ajax_views.search, name='ajax-search'),
]
