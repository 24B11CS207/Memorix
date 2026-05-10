from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('instant/', views.instant_index, name='instant'),
    path('instant/history/', views.instant_history, name='history'),
    path('instant/start/<int:topic_id>/', views.start_instant, name='start'),
    path('instant/take/<int:test_id>/', views.take_instant, name='take'),
    path('instant/result/<int:test_id>/', views.instant_result, name='result'),
]
