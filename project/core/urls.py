from django.urls import path
from . import views

app_name="core"
urlpatterns=[path("",views.home,name="home"), 
             path("encounters", views.add_combatant, name="add_combatant"),
             path("combatants/<int:entry_id>/move/", views.move_combatant, name="move_combatant"),
             path("quests/", views.add_quest, name="add_quest"),
             path("quests/<int:quest_id>/", views.quest_detail, name="quest_detail")]
