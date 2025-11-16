from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

STATIC_DIR = "static"
TEMPLATES_DIR = "templates"
DB_PATH = "db.sqlite3"

static_files = StaticFiles(directory=STATIC_DIR)
templates = Jinja2Templates(directory=TEMPLATES_DIR)
