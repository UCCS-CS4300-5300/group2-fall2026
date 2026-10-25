# Encounter Helper

A small Django dashboard for setting up a D&D encounter. You can add combatants,
move their cards around, roll dice from the Log tab, and save quests or notes.

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

For Sprint 1, use a fresh checkout and database. Earlier migration files were
changed, so upgrading an older local database is not supported yet. Keep any
older database as a backup; do not delete it to get the app running.

## Quests and notes

Use the Quests tab to add a quest or note, check it off, reopen it, or delete it.
Text is limited to 500 characters. Entries and completion status are saved in
the database with the current placeholder encounter, so they survive a reload.
They do not change combatant stats or dice rolls.

Run `python manage.py migrate` after pulling this change to add the quest table.
The Django tests cover saving, completion, deletion, validation, and CSRF.

## Dice roller

Choose d4, d6, d8, d10, d12, or d20 and roll between 1 and 20 dice. JavaScript
checks the inputs and rolls the dice in the browser, without a server request.
Results appear in the Log tab. Roll history only lasts until the page is reloaded;
it does not change HP or initiative.

Other frontend features can import `rollDice(sides, count)` from `dice.js`.
It takes numbers and returns `{ sides, count, rolls, total }`. It does not update
the page or save character data. The old `/dice/roll/` endpoint is removed.

## AI chats

Install and start [Ollama](https://ollama.com/), then download the models used
by each chat:

```bash
ollama pull qwen3:8b
ollama pull qwen3:4b
```

The Python Ollama client is installed with `pip install -r requirements.txt`.
This is a client library; you still need to install and run the Ollama
application separately.

The AI DM Co-Pilot uses `qwen3:8b`; the Rules Lawyer uses `qwen3:4b`. Requests
go through Django to Ollama at `http://127.0.0.1:11434`. Set `OLLAMA_DM_MODEL`
or `OLLAMA_RULES_MODEL` to override the model for either chat, and set
`OLLAMA_BASE_URL` if Ollama uses a different address.

The Rules Lawyer only answers from a PDF reference. By default it uses
`project/local_data/DnD5e_SRD.pdf`, which is included in the local project
setup. It retrieves relevant text from the PDF, asks the model to cite the PDF
page for rules claims, and declines to make a ruling if it finds no relevant
text.

Chat history is held in the page and is cleared when it is reloaded. The two
chat tabs use separate histories and prompts. Ollama must be running while you
use either chat.

## Tests

```bash
python -m pytest -q
python manage.py check
npm test
```

Use Node.js 24 for `npm test`; there are no npm packages to install. The JavaScript
tests cover dice choices, limits, totals, and invalid inputs with fixed random
values. The Django tests cover the dice controls, CSRF, adding combatants, saved
card positions, and separate character state between encounters.

GitHub Actions runs both test suites, Django checks, and migrations on pull requests
and pushes to main. The workflow is in `.github/workflows/tests.yml`.

## Current limits

The dashboard still uses one placeholder encounter. The player/enemy selector
does not change the saved character type yet. Initiative, attacks, next turn,
clear encounter, and AI chat are not implemented. Character cards and
their positions are saved in the local SQLite database. Bootstrap loads from a
CDN, so the styling and modal need an internet connection.

## Development notes

AI assistance was used during development and testing. The automated tests
passed, and the main functionality was checked in the browser. These changes
still need team review before merging.
