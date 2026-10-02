from django.urls import path
from . import views

app_name="core"
urlpatterns = [
	path("", views.home, name="home"),
	path("encounters/<int:encounter_id>/", views.encounter_detail, name="encounter_detail"),
]
