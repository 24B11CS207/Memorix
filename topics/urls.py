from django.urls import path
from . import views

app_name = 'topics'

urlpatterns = [
    path('', views.TopicListView.as_view(), name='list'),
    path('new/', views.TopicCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TopicDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', views.topic_delete, name='delete'),
    path('<int:topic_id>/module/<int:module_id>/', views.module_view, name='module'),
    path('<int:topic_id>/module/<int:module_id>/quiz/', views.module_quiz, name='module_quiz'),
]
