from django.urls import path
from wbcore import ajax_views

ajax_patterns = [
    path('filter-news/', ajax_views.filter_news, name='ajax-filter-news'),
    path('search/<str:query>/', ajax_views.search, name='ajax-search'),
]

