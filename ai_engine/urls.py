from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('chatbot/', views.chatbot_page, name='chatbot'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    # Memorix standalone frontend — no session auth required
    path('api/tutor/',     views.api_tutor,     name='api_tutor'),
    path('api/questions/', views.api_questions, name='api_questions'),
    path('api/content/',   views.api_content,   name='api_content'),
    path('api/mock/',      views.api_mock,       name='api_mock'),
]
