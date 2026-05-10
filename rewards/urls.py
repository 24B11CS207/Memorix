from django.urls import path
from . import views

app_name = 'rewards'

urlpatterns = [
    path('', views.rewards_home, name='home'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]
