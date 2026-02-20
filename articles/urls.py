from django.urls import path
from . import views

urlpatterns = [
    path('', views.test_view),
    path('create/', views.article_create),
    path('<int:pk>/delete/', views.article_delete),
]