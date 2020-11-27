from flask import render_template, request, flash
from flask_login import login_required
from flask_wtf.csrf import validate_csrf

from wtforms.validators import ValidationError

from webapi.libs.network import is_up
from webapi.libs.text import camel_case
from webapi.libs.api.response import redirect_or_response

from .. import bp, name
from .forms import create_data_form, create_settings_form
from .caspar_connector import is_caspar_up
from .backend_connector import backend_request


@bp.route('/', methods=['POST', 'GET'])
@bp.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():
    """
    Create a dashboard page.

    :return:
    """
    from .. import config

    # Create default config values
    _init_server_config()

    # Create the server settings form
    settings = create_settings_form(config)

    # Save config values if submitted
    if settings.validate_on_submit():
        _set_server_config(settings.server.data, settings.overlay_server.data)

    # Read config values
    server, port = _get_caspar_server_and_port()

    if not is_up(server):
        # Check if server is not reachable
        flash(f"Server {server} is not reachable")
        reachable = False
    elif not is_caspar_up(server, port):
        # Check if CasparCG server is not reachable
        flash(f"CasparCG server on route {server} port {port} not reachable")
        reachable = False
    else:
        reachable = True

    # If a form was submitted, check the csrf token for security
    validated = False
    if request.form.get('csrf_token'):
        try:
            validate_csrf(request.form.get('csrf_token'))
            validated = True
        except ValidationError as e:
            flash(f'ValidationError: {e}')

    if reachable and validated:
        backend_request(request.form.to_dict())

    # MAGIC Parse routes file to get form values
    from .. import definitions
    defs = dict()
    for e in dir(definitions):
        if e.endswith('_definition'):
            defs[e.replace('_definition', '')] = getattr(definitions, e)

    def_list = list(defs.keys())

    form_list = list()
    for e in defs:
        # Create the form for the overlay and save it
        form = create_data_form(defs[e], e)
        form_list.append((camel_case(e, '_'), form))

    return render_template('overlay_dashboard.html', settings=settings, forms=form_list)


def _init_server_config():
    from .. import config
    config.set_if_none(name, 'server', 'localhost:5250')
    config.set_if_none(name, 'casparcg_server', 'http://localhost:5000/overlay/')


def _set_server_config(server: str, overlay_server: str):
    from .. import config
    if '://' in server:
        server = server.split('://')[1]
    config.set(name, 'server', server)
    config.set(name, 'casparcg_server', overlay_server)


def _get_caspar_server_and_port() -> tuple:
    from .. import config
    return config.get(name, 'server').split(':')
