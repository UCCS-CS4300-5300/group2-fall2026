from django.shortcuts import render
from .models import Character

def home(request):
    return render(
        request,
        "core/home.html",
        {
            "items": None
        }
    )

# View to add combatant to encounter.
def add_combatant(request):
    pass