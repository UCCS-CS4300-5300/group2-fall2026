from django.urls import path
from .views import npc

app_name = "npcs"
urlpatterns = [
    path("<int:encounter_id>", npc.npcs, name="npc_list"),
    path("<int:npc_id>/", npc.npc_detail, name="npc_detail"),
]
