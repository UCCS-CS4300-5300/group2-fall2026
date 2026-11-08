from django.urls import path
from . import npc_views

app_name = "npcs"
urlpatterns = [
    path("", npc_views.npcs, name="list"),
    path("<int:npc_id>/", npc_views.npc_detail, name="detail"),
]
