from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('chatbot/', views.chatbot_page, name='chatbot'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
]
