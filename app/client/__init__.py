from flask import Blueprint
from flask_assets import Environment, Bundle
import yaml

client_bp = Blueprint("client", __name__, template_folder="templates", static_folder="static")

from app.client.routes import main
from app.client.routes.orders import orders, order_details, new_order
from app.client.routes.payment import payment
