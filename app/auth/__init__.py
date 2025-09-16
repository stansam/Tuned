from flask import Blueprint
from flask_assets import Environment, Bundle
import yaml
import os

auth_bp = Blueprint("auth", __name__, template_folder="templates", static_folder="static")

from app.auth.routes import main
from app.auth.routes.pass_reset import reset
from app.auth.routes.register import register
