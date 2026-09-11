from django.urls import path
from .views import session_list

urlpatterns = [path("", session_list, name="session-list")]
