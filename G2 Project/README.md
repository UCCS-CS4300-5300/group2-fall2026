# HW1 — Python to Django: Your First Feature

Starter repository for CS 4300/5300 Advanced Software Engineering.

This starter contains:

- Python foundation exercises with provided tests
- A small Django Study Session Tracker
- Beginner hints for navigating Django
- Starter automated tests
- GitHub Codespaces configuration

## Recommended: GitHub Codespaces

Open the repository in GitHub, choose **Code → Codespaces → Create codespace on main**.

When setup finishes:

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Open the forwarded port for 8000.

Run tests with:

```bash
pytest
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000/.

## Assignment workflow

Students should copy the starter contents into the `hw1/` folder of their private course repository and work there.

The Canvas assignment contains the authoritative requirements and Git checkpoints.
