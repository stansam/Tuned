from flask import Blueprint

bp = Blueprint("sitemap_robots", __name__)

from app.sitemap_robots.routes import main