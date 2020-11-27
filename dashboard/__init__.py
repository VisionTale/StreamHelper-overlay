from flask import render_template, request
from flask_login import login_required

from . import settings, rundown, definitions
from .. import bp, name, config, logger

from webapi.libs.api.response import response

rundown.load_rundowns()


@bp.route('/', methods=['POST', 'GET'])
@bp.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():
    """
    Create a dashboard page.

    :return: rendered overlay page
    """
    return render_template('overlay_dashboard.html',
                           name=name,
                           caspar=config.get_or_set(name, 'use_caspar', 'false'),
                           caspar_server_url=config.get_or_set(name, 'caspar_server',
                                                               request.url_root.split('/')[2].split(':')[0] + ':5250'),
                           overlay_server_url=config.get_or_set(name, 'overlay_server',
                                                                request.base_url.rstrip(name + '/dashboard')),
                           current_rundown_name=rundown.get_current_rundown_name(),
                           current_rundown=rundown.get_current_rundown(),
                           rundowns=rundown.get_rundowns(),
                           definitions=definitions.get_definitions()
                           )


@bp.route('/definitions/edit')
def edit_definitions():
    """
    Editor for the definitions file, identified by definitions.get_definitions_file().

    :return: rendered file editor, or error page if file is not set or not read or writeable
    """
    from .definitions import get_definitions_file
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
        return response(400, 'File error: ' + str(e), graphical=True)
    return render_template('edit_definitions.html', name=name, file_content=file_content)
