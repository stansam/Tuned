from flask import Blueprint

main_bp = Blueprint("main", __name__, template_folder="templates", static_folder="static", static_url_path="/static/main")

from app.main.routes import main
from app.main.routes.services import services
from app.main.routes.samples import samples
from app.main.routes.blogs import blogs