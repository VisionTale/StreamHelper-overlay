from flask import Blueprint

from webapi.libs.config import Config
from webapi.libs.log import Logger
from webapi.libs.system import create_folder

description: str = "Get overlays for CasparCG, OBS and more"

bp: Blueprint = None
name: str = None
logger: Logger = None
config: Config = None
provides_pages: list = [
    ('Overlay', 'dashboard')
]
settings_folder: str = None


def set_blueprint(blueprint: Blueprint):
    """
    Plugins factory method to set a blueprint.

    :param blueprint:
    """
    global bp, settings_folder
    bp = blueprint

    from os.path import join, isdir
    from pathlib import Path

    settings_folder = join(config.get('webapi', 'data_dir'), 'overlay')
    create_folder(settings_folder)

    from . import dashboard, api
