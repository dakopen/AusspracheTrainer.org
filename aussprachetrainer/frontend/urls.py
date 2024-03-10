from django.urls import path
from .views import index, legal_notice, privacy_policy, initiate_analysis, check_status, \
                   analysis_error, change_language, generate_random_sentence, robots_txt, text_to_speech, \
                   about_page
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='index'), # Render index at the root URL
    path('change_language/', change_language, name='change_language'),
    path('legal_notice/', legal_notice, name='legal_notice'),
    path('privacy_policy/', privacy_policy, name='privacy_policy'),
    path('analyze/', initiate_analysis, name='initiate_analysis'),
    path('check_status/<str:task_id>/', check_status, name='check_status'),
    path('analysis_error/', analysis_error, name='analysis_error'),
    path('generate_random_sentence/', generate_random_sentence, name='generate_random_sentence'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('speech_synthesis/', text_to_speech, name='text_to_speech'),
    path('about/', about_page, name='about'),
    # other URL patterns...
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)