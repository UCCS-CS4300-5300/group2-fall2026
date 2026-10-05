# Encounter Helper

A small Django dashboard for setting up a D&D encounter. You can add combatants,
move their cards around, and roll dice from the Log tab.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Run these commands from the `project/` directory. Open the local address printed
by `runserver`.

## Dice roller

Choose d4, d6, d8, d10, d12, or d20 and roll between 1 and 20 dice. The server
checks the inputs and returns each roll plus the total. Results appear in the
Log tab. Roll history only lasts until the page is reloaded; it does not change
HP or initiative.

## Tests

```bash
python -m pytest -q
python manage.py check
```

The tests cover dice choices and totals, invalid inputs, request methods, CSRF,
adding combatants, saved card positions, and separate character state between
encounters. Random rolls are patched in the tests so the expected results are
repeatable.

GitHub Actions runs the tests, Django checks, and migrations on pull requests
and pushes to main. The workflow is in `.github/workflows/tests.yml`.

## Current limits

The dashboard still uses one placeholder encounter. The player/enemy selector
does not change the saved character type yet. Initiative, attacks, next turn,
clear encounter, quests, and AI chat are not implemented. Character cards and
their positions are saved in the local SQLite database. Bootstrap loads from a
CDN, so the styling and modal need an internet connection.

## Development notes

AI assistance was used during development and testing. The automated tests
passed, and the main functionality was checked in the browser. These changes
still need team review before merging.
