from flask import Blueprint 

admin_bp = Blueprint("admin", __name__, template_folder="templates", static_folder="static")

from app.admin.routes import main
from app.admin.routes.blogs import blogs 
from app.admin.routes.testimonials import testimonials
from app.admin.routes.samples import samples
from app.admin.routes.orders import orders
from app.admin.routes.payments import payment
from app.admin.routes.services import services
from app.admin.routes.users import users