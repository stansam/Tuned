from flask import Blueprint

api_bp = Blueprint('api', __name__)

from app.api.routes import homepage, calculate_price, profile_pic
from app.api.routes.client.chats import chat_modal
from app.api.routes.admin import dashboard
from app.api.routes.admin.blogs import blogs
from app.api.routes.admin.samples import samples
from app.api.routes.admin.orders import orders
from app.api.routes.admin.services import services
from app.api.routes.client.orders import order_activities
from app.api.routes.client.payment import payment
from app.api.routes.client.profile import profile