from fastapi.templating import Jinja2Templates
from pathlib import Path

# Calcula o caminho da raiz do projeto:
# app/templating.py -> parent = app -> parent = raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Define onde está a pasta templates
TEMPLATES_DIR = BASE_DIR / "templates"

# Cria a instância única que será usada em todo o projeto
templates = Jinja2Templates(directory=TEMPLATES_DIR)