# Beginner Guide — HW1

Use this only when you need it. You do not have to read it front-to-back.

## Part 1: Python

Run only the Python exercises:

```bash
pytest python_foundations -q
```

A useful workflow is:

1. Read one function's docstring.
2. Find its test in `python_foundations/test_exercises.py`.
3. Implement the smallest behavior that satisfies the requirement.
4. Run the tests again.
5. Read failures before changing code.

Useful Python reminders:

```python
text.strip()
text.lower()
text.replace(" ", "-")
```

Raise an error:

```python
raise ValueError("message")
```

Filter a list:

```python
result = [item for item in items if some_condition]
```

## Part 2: Finding Your Way Through Django

The application flow is:

```text
Browser request
    ↓
sessions/urls.py
    ↓
sessions/views.py
    ↓
sessions/models.py and sessions/forms.py
    ↓
sessions/templates/sessions/session_list.html
    ↓
Browser response
```

You do not need to understand all of Django yet.

## Part 3: Adding Subject

You will need to touch several layers.

### Model

Open `sessions/models.py`.

A Django text field can look like:

```python
name = models.CharField(max_length=100)
```

After changing a model:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Form

Open `sessions/forms.py`.

The `fields` list controls which model fields appear in the form.

### Template

Open `sessions/templates/sessions/session_list.html`.

Django template variables look like:

```django
{{ session.topic }}
```

## Part 4: Negative Duration

`StudySession.clean()` is intentionally unfinished.

Django validation can raise:

```python
from django.core.exceptions import ValidationError
raise ValidationError("Duration cannot be negative.")
```

In a test, you can check for that with:

```python
with pytest.raises(ValidationError):
    session.full_clean()
```

You still need to decide the exact condition that belongs in the implementation.

## Common commands

Run everything:

```bash
pytest
```

Run only Python foundation tests:

```bash
pytest python_foundations -q
```

Run only Django model tests:

```bash
pytest sessions/tests/test_models.py -q
```

Start Django:

```bash
python manage.py runserver 0.0.0.0:8000
```

Stop the server with Ctrl+C.
