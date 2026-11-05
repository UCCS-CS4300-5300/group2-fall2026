from django.urls import path
from . import views

app_name="core"
urlpatterns=[
    path("",views.dashboard,name="dashboard"), 
    path("encounter/<int:encounter_id>",views.encounter_detail, name="encounter"), 
    path("encounter/",views.add_encounter,name="add_encounter"),
    path("api/enemies/", views.search_enemy, name="search_enemy"),
    path("api/enemies/import/", views.import_enemy, name="import_enemy"),
    path("chat/", views.chat, name="chat"),
    path("encounter/<int:encounter_id>/combatants/", views.add_combatant, name="add_combatant"),
    path("combatants/<int:entry_id>/", views.move_combatant, name="move_combatant"),
    path("encounter/<int:encounter_id>/quests/", views.add_quest, name="add_quest"),
    path("quests/<int:quest_id>", views.quest_detail, name="quest_detail"),
    path("character/<int:entry_id>/hp/", views.update_hp, name="update_hp"),
    path("character/<int:entry_id>/initiative/", views.update_initiative, name="update_initiative")
]
