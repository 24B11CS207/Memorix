from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
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
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
