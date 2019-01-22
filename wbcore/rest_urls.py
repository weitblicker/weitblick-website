from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from wbcore import rest_views

rest_patterns = [
    path('unions', rest_views.host_list),
    path('unions/<int:pk>/', rest_views.host_detail),

    path('projects', rest_views.project_list),
    path('projects/<int:pk>/', rest_views.project_detail),

    path('events', rest_views.event_list),
    path('events/<int:pk>/', rest_views.event_detail),

    path('posts', rest_views.post_list),
    path('posts/<int:pk>/', rest_views.post_detail),
]

rest_patterns = format_suffix_patterns(rest_patterns)
