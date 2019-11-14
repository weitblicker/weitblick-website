from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from wbcore import rest_views

rest_patterns = [
    path('unions/', rest_views.host_list, name="rest-unions"),
    path('unions/<str:pk>/', rest_views.host_detail, name="host-detail"),

    path('projects/', rest_views.project_list, name="rest-projects"),
    path('projects/<int:pk>/', rest_views.project_detail, name="rest-project"),

    path('events/', rest_views.event_list, name="rest-events"),
    path('events/<int:pk>/', rest_views.event_detail, name="rest-event"),

    path('news/', rest_views.news_list, name="rest-news-posts"),
    path('news/<int:pk>/', rest_views.news_detail, name="rest-news-post"),

    path('blog/', rest_views.blog_list, name="rest-blog-posts"),
    path('blog/<int:pk>/', rest_views.blog_detail, name="rest-blog-post"),

    path('locations/', rest_views.location_list, name="rest-blog-posts"),
    path('blog/<int:pk>/', rest_views.location_detail, name="rest-blog-post"),

    path('auth/', include('rest_auth.urls')),
    path('auth/registration/', include('rest_auth.registration.urls'))
    #path('users', include('users.', )
]

rest_patterns = format_suffix_patterns(rest_patterns)
