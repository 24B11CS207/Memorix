from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('manifest.webmanifest', TemplateView.as_view(template_name='manifest.webmanifest', content_type='application/manifest+json'), name='manifest'),
    path('service-worker.js', TemplateView.as_view(template_name='service-worker.js', content_type='application/javascript'), name='service_worker'),
    path('static/js/pwa.js', TemplateView.as_view(template_name='static/js/pwa.js', content_type='application/javascript'), name='pwa_js'),
    path('static/img/memorix-icon.svg', TemplateView.as_view(template_name='static/img/memorix-icon.svg', content_type='image/svg+xml'), name='memorix_icon'),
    path('index.html', TemplateView.as_view(template_name='index.html'), name='legacy_index'),
    path('dashboard.html', TemplateView.as_view(template_name='dashboard.html'), name='legacy_dashboard'),
    path('classes.html', TemplateView.as_view(template_name='classes.html'), name='legacy_classes'),
    path('subjects.html', TemplateView.as_view(template_name='subjects.html'), name='legacy_subjects'),
    path('learning-mode.html', TemplateView.as_view(template_name='learning-mode.html'), name='legacy_learning_mode'),
    path('topics-page.html', TemplateView.as_view(template_name='topics-page.html'), name='legacy_topics_page'),
    path('learn-module.html', TemplateView.as_view(template_name='learn-module.html'), name='legacy_learn_module'),
    path('module-test.html', TemplateView.as_view(template_name='module-test.html'), name='legacy_module_test'),
    path('deep-dive.html', TemplateView.as_view(template_name='deep-dive.html'), name='legacy_deep_dive'),
    path('ai-tutor.html', TemplateView.as_view(template_name='ai-tutor.html'), name='legacy_ai_tutor'),
    path('django-home/', TemplateView.as_view(template_name='home.html'), name='django_home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('topics/', include('topics.urls', namespace='topics')),
    path('exams/', include('exams.urls', namespace='exams')),
    path('revisions/', include('revisions.urls', namespace='revisions')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('notes/', include('notes.urls', namespace='notes')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('rewards/', include('rewards.urls', namespace='rewards')),
    path('ai/', include('ai_engine.urls', namespace='ai_engine')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
