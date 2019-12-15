from django.urls import path, include
from rest_auth.registration.views import VerifyEmailView, RegisterView
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
    path('locations/<int:pk>/', rest_views.location_detail, name="rest-blog-post"),

    path('cycle/donations/', rest_views.cycle_donations_list, name="rest-cycle-donations"),
    path('cycle/segment/', rest_views.cycle_add_segment, name="rest-cycle-add-segment"),
    path('cycle/tours/', rest_views.cycle_user_tours, name="rest-cycle-user-tours"),
    path('cycle/ranking/', rest_views.cycle_ranking, name="rest-cycle-ranking"),
    #path('cycle//', rest_views.UserrankingViewSet.as_view({'get': 'list'}), name="rest-cycle-userrank"),

    path('auth/', include('rest_auth.urls')),
    path('auth/registration/', RegisterView.as_view(), name='rest_register'),
    path('auth/registration/verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path('auth/registration/account-confirm-email/<str:key>/', rest_views.account_confirm_email, name='account_confirm_email'),

    path('upload/', rest_views.markdown_uploader, name='markdown_uploader_page'),
    path('faq/', rest_views.FAQViewSet.as_view({'get': 'list'}), name='rest-faq'),
]

rest_patterns = format_suffix_patterns(rest_patterns)
