from django.urls import path
from . import npc_views

app_name = "npcs"
urlpatterns = [
    path("<int:encounter_id>", npc_views.npcs, name="npc_list"),
    path("<int:npc_id>/", npc_views.npc_detail, name="npc_detail"),
]
