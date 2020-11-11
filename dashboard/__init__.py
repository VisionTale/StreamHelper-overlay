from flask import render_template, request
from flask_login import login_required

from . import settings
from .. import bp, name, config, logger

from webapi.libs.api.response import redirect_or_response, response


@bp.route('/', methods=['POST', 'GET'])
@bp.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():
    """
    Create a dashboard page.
    :return:
    """
    return render_template('overlay_dashboard.html',
                           name=name,
                           caspar=config.get_or_set(name, 'use_caspar', 'false'),
                           caspar_server_url=config.get_or_set(name, 'caspar_server',
                                                               request.url_root.split('/')[2].split(':')[0] + ':5250'),
                           overlay_server_url=config.get_or_set(name, 'overlay_server',
                                                                request.base_url.rstrip('/dashboard')),
                           current_rundown=config.get_or_set(name, 'current_rundown', '')
                           )


@bp.route('/definitions/edit')
def edit_definitions():
    """
    Edit a given file.
    :return:
    """
    from ..api.definitions import get_definitions_file
    from os.path import isfile
    from json import dump

    try:
        if not isfile(get_definitions_file()):
            if get_definitions_file() == '':
                raise IOError('No definitions filepath set')
            with open(get_definitions_file(), 'w') as f:
                dump({}, f)
        with open(get_definitions_file(), 'r') as f:
            file_content = [line for line in f.readlines() if line != '\n']
    except IOError as e:
        return response(request, 400, 'File error: ' + str(e), graphical=True)
    return render_template('edit_definitions.html', name=name, file_content=file_content)

