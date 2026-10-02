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
