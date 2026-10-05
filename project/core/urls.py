from django.urls import path
from . import views

app_name="core"
urlpatterns=[path("",views.home,name="home"), 
             path("dice/roll/", views.roll_dice, name="roll_dice"),
             path("encounters", views.add_combatant, name="add_combatant"),
             path("combatants/<int:entry_id>/move/", views.move_combatant, name="move_combatant")]
