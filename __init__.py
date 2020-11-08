from flask import Blueprint

from webapi.libs.config import Config
from webapi.libs.log import Logger

description: str = "Get overlays for CasparCG, OBS and more"

bp: Blueprint = None
name: str = None
logger: Logger = None
config: Config = None
provides_pages: list = [
    ('Overlay', 'dashboard')
]


def set_blueprint(blueprint: Blueprint):
    global bp
    bp = blueprint

    from . import dashboard, api

    api.definitions.create_routes()
