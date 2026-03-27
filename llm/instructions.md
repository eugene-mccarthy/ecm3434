# LLM Instructions & Recommendations

This directory contains guidance for using LLMs (e.g. Claude, GPT-4) when working on this project.

---

## Project Overview

A Flask web application. Routes are defined in `app/routes.py`, templates in `app/templates/`, and static assets in `app/static/`.

## Coding Conventions

- Follow PEP 8 for Python code.
- Use Flask Blueprints to group related routes.
- Keep business logic out of route handlers — move it to separate modules under `app/`.
- Templates extend `base.html`.

## Suggested Prompts

### Adding a new route
> "Add a `/contact` route to `app/routes.py` that renders a new `contact.html` template extending `base.html`."

### Adding a model / database
> "Add SQLAlchemy to this project. Create a `User` model with `id`, `username`, and `email` fields. Wire it up in `app/__init__.py`."

### Writing a test
> "Write a pytest test in `tests/` that checks the `/` route returns a 200 status code using the Flask test client."

### Adding a form
> "Add a WTForms contact form to the `/contact` route with `name`, `email`, and `message` fields, with server-side validation."

## Cautions

- Do not commit `.env` — it contains secrets.
- Run `pytest` before committing.
- Keep `requirements.txt` up to date when adding packages (`pip freeze > requirements.txt` or pin manually).
