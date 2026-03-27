# ECM3434

A basic Flask web application.

## Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and set a real SECRET_KEY
```

## Running

```bash
python run.py
```

Visit [http://localhost:5000](http://localhost:5000).

## Project Structure

```
ecm3434/
├── app/
│   ├── __init__.py        # App factory
│   ├── routes.py          # Route handlers
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── base.html
│       ├── index.html
│       └── about.html
├── tests/
│   └── test_routes.py     # pytest tests
├── llm/
│   └── instructions.md    # LLM guidance for this project
├── config.py              # Config classes
├── run.py                 # Entry point
├── requirements.txt
├── .env                   # Local secrets (not committed)
└── .env.example           # Template for .env
```

## Testing

```bash
pytest
```

## LLM Instructions

See [`llm/instructions.md`](llm/instructions.md) for guidance on using AI assistants with this project.
