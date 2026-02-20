from django.urls import path
from .views import create_workspace     

from . import views
urlpatterns = [
    path('create/', create_workspace, name='create-workspace'),
]