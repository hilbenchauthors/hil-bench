from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR), undefined=StrictUndefined)
