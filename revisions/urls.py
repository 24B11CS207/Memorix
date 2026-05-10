from django.urls import path
from . import views

app_name = 'revisions'

urlpatterns = [
    path('', views.revisions_index, name='index'),
    path('plan/create/', views.create_plan, name='create_plan'),
    path('plan/<int:plan_id>/', views.plan_detail, name='plan_detail'),
    path('session/<int:session_id>/', views.take_review, name='take_review'),
    path('session/<int:session_id>/result/', views.review_result, name='result'),
]
