from django.shortcuts import redirect, render
from .forms import StudySessionForm
from .models import StudySession


def session_list(request):
    """Show saved study sessions and allow a new one to be created."""
    if request.method == "POST":
        form = StudySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.full_clean()
            session.save()
            return redirect("session-list")
    else:
        form = StudySessionForm()

    sessions = StudySession.objects.order_by("-completed_on", "-id")
    return render(request, "sessions/session_list.html", {"sessions": sessions, "form": form})
