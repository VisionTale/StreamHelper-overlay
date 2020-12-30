from flask import request, flash, render_template

from webapi.libs.api.response import redirect_or_response
from webapi.libs.api.parsing import param, is_set
from webapi.libs.text import camel_case

from .. import bp, config, name, logger, settings_folder
from .rundown import add_to_current_rundown, remove_from_current_rundown, rename_in_current_rundown

url_prefix: str = '/actions'
actions: dict = {}


@bp.route(f'{url_prefix}/add', methods=['GET', 'POST'])
def add_action():
    """
    Add a action to the current rundown. A UUID will be assigned to the action.

    Arguments:
        - uuid

    :return: redirect or response
    """

    action = param('name')
    if not is_set(action):
        return redirect_or_response(400, 'Missing parameter name')

    try:
        add_to_current_rundown(action)
    except AttributeError as e:
        return redirect_or_response(400, e.msg)

    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/remove', methods=['GET', 'POST'])
def remove_action():
    """
    Remove a action from the current rundown based on it's uuid.

    Arguments:
        - uuid

    :return: redirect or response
    """
    uuid = param('uuid')
    if not is_set(uuid):
        return redirect_or_response(400, 'Missing parameter uuid')

    try:
        remove_from_current_rundown(uuid)
    except AttributeError as e:
        return redirect_or_response(400, e.msg)

    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/rename', methods=['GET', 'POST'])
def rename_action():
    """
    Rename a action from the current rundown based on it's uuid.

    Arguments:
        - uuid
        - name

    :return: redirect or response
    """
    uuid = param('uuid')
    if not is_set(uuid):
        return redirect_or_response(400, 'Missing parameter uuid')
    display_name = param('name')
    if not is_set(display_name):
        return redirect_or_response(400, 'Missing parameter name')

    try:
        rename_in_current_rundown(uuid, display_name)
    except AttributeError as e:
        return redirect_or_response(400, e.msg)

    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/show', methods=['GET', 'POST'])
def show_action():
    """
    Rendered template file.

    All arguments except of the filename argumeent are passed to the file.

    Arguments:
        - filename

    :return: rendered file
    """
    values: dict = request.args.to_dict() or request.form.to_dict()
    action = values.pop('filename', '')
    if not is_set(action):
        return response(400, 'Missing parameter filename', graphical=True)
    from os.path import isfile, join
    if not isfile(join(bp.template_folder, 'overlays', action)):
        return response(404, 'Action file not found', graphical=True)

    return render_template(f'overlays/{action}', **values)


@bp.route(f'{url_prefix}/reload', methods=['GET'])
def reload_actions():
    """
    Reload actions file.

    :return: redirect or response
    """
    from json.decoder import JSONDecodeError
    try:
        _load_actions_file()
        return redirect_or_response(200)
    except (SyntaxError, JSONDecodeError) as e:
        return redirect_or_response(400, e.msg)


@bp.route(f'{url_prefix}/save_content', methods=['POST'])
def save_actions_file_content():
    """
    Save file content of actions.json.

    Arguments:
        - content, encoded file content

    :return: redirect or response
    """
    from urllib.parse import unquote
    content = unquote(request.form.get('content'))

    create_empty_actions_file()
    with open(get_actions_file(), 'w') as f:
        f.write(content)

    return redirect_or_response(200)


def _load_actions_file():
    """
    Load the actions file.

    :exception SyntaxError: If validation check fails
    :exception json.decoder.JSONDecodeError: If json.load fails
    """
    actions.clear()
    create_empty_actions_file()
    with open(get_actions_file(), 'r') as f:
        from json import load
        content: dict = load(f)
    if not type(content) == dict:
        raise SyntaxError('Content is not a json object')
    for file_def in content:
        if not type(content[file_def]) == dict:
            raise SyntaxError(f'Content of {file_def} is not a valid json array')
        if 'filename' not in content[file_def].keys() or type(content[file_def]['filename']) != str:
            raise SyntaxError(f'Content of {file_def} misses the filename attribute')
        if 'fields' in content[file_def].keys():
            if type(content[file_def]['fields']) != list:
                raise SyntaxError(f'Content of {file_def} has fields attribute but is no list')
        if 'groups' in content[file_def].keys():
            if type(content[file_def]['fields']) != list:
                raise SyntaxError(f'Content of {file_def} has groups attribute but is no list')
            for group in content[file_def]['groups']:
                if type(group) != dict:
                    raise SyntaxError(f'Content of {file_def} has a group which is no dictionary (json object)')
                if 'name' not in group.keys():
                    raise SyntaxError(f'Content of {file_def} has a group which has no name attribute')

        if 'display_name' not in content[file_def].keys():
            content[file_def]['display_name'] = camel_case(file_def, '_')
        actions[file_def] = content[file_def]


def get_actions_file() -> str:
    """
    Get the current actions filepath from plugins actions_file config value.

    :return: full qualified filepath
    """
    from os.path import join
    return config.get_or_set(name,
                             'actions_file',
                             join(settings_folder, 'actions.json')
                             )


def create_empty_actions_file():
    """
    Creates the file (and the corresponding folder) for the actions.

    :return:
    """
    from os.path import dirname, isdir, isfile
    if not isdir(dirname(get_actions_file())):
        from pathlib import Path
        Path(dirname(get_actions_file())).mkdir(parents=True)
    if not isfile(get_actions_file()):
        from json import dump
        with open(get_actions_file(), 'w') as f:
            dump({}, f)


def get_actions() -> dict:
    """
    Reloads and returns all actions from the file returned by get_actions_file()

    :return: dict of actions
    """
    global actions
    from json.decoder import JSONDecodeError
    try:
        _load_actions_file()
    except (SyntaxError, JSONDecodeError) as e:
        flash("Syntax or decoding error: " + str(e))
        actions = {}
    return actions


def set_actions_file(filepath: str):
    """
    Set a new actions filepath to plugins actions_file config value.

    :param filepath: full qualified filepath
    """
    config.set(name, 'actions_file', filepath)
