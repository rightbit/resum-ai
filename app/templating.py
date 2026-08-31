"""Shared Jinja2Templates instance for the application."""
from pathlib import Path

from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Jinja2Templates autoescapes .html templates by default, which protects
# rendered visitor-supplied content (name, company, questions) from
# injection when displayed back in the profile/chat/admin views.
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
