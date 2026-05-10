from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.notes_list, name='list'),
    path('new/', views.note_create, name='create'),
    path('<int:pk>/edit/', views.note_edit, name='edit'),
    path('<int:pk>/delete/', views.note_delete, name='delete'),
]
