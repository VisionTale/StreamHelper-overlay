from flask import request, flash, render_template
from jsonschema import validate

from webapi.libs.api.response import redirect_or_response
from webapi.libs.api.parsing import param, is_set
from webapi.libs.text import camel_case

from .. import bp, config, name, logger, settings_folder
from ..libs.actions_schema import actions_schema
from .rundown import add_to_current_rundown, remove_from_current_rundown, rename_in_current_rundown, get_rundowns, \
    get_current_rundown_name

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

    All arguments are also passed to the file.

    Arguments:
        - filename
        - rundown, name of the rundown
        - action, uuid of the action that stores all values

    :return: rendered file
    """

    rundown_name = param('rundown', get_current_rundown_name())
    if not is_set(rundown_name):
        return redirect_or_response(400, 'Missing parameter rundown')
    if rundown_name not in get_rundowns():
        return redirect_or_response(400, 'Rundown name unknown')
    rundown = get_rundowns()[rundown_name]

    action_uuid = param('action')
    if not is_set(action_uuid):
        return redirect_or_response(400, 'Missing parameter action')
    action: dict = None

    for e in rundown['rundown']:
        if e['id'] == action_uuid:
            action = e
    if not action:
        return redirect_or_response(400, "Actions uuid unknown")

    values: dict = request.args.to_dict() or request.form.to_dict()
    if action['name'] in rundown['global']:
        for group in rundown['global'][action['name']]:
            values = {**values, **rundown['global'][action['name']][group]}

    values = {**values, **action['values']}

    for field in get_actions()[action['name']].get('fields', []):
        if field[0] not in values:
            values[field[0]] = field[1]
    for group in get_actions()[action['name']].get('groups', []):
        for field in group.get('fields', []):
            if field[0] not in values:
                values[field[0]] = field[1]

    from os.path import isfile, join
    filename: str = get_actions()[action['name']]['filename']

    if not isfile(join(bp.template_folder, 'overlays', filename)):
        return response(404, 'Action template file not found', graphical=True)

    return render_template(f'overlays/{filename}', **values)


def get_update_params(rundown_name: str, action_uuid: str, func: str) -> dict:
    """
    Gathers and returns a dictionary of key value pairs that represent the values saved for a given update function.

    :param rundown_name: name of the rundown
    :param action_uuid: uuid of the selected action
    :param func: name of the function to be executed

    :return: key value dict (string pairs)
    :raises ValueError: if action_uuid is invalid
    """
    if rundown_name not in get_rundowns():
        return redirect_or_response(400, 'Rundown name unknown')
    rundown = get_rundowns()[rundown_name]

    action: dict = None
    for e in rundown['rundown']:
        if e['id'] == action_uuid:
            action = e
    if not action:
        raise ValueError('Invalid action uuid')

    if func == "fadeout":
        pass #TODO Add fadeout parameter passing

    values: dict = {}
    if 'updates' in action.keys() and func in action['updates'].keys():
        values = action['updates'][func].copy()

    for update in get_actions()[action['name']].get('updates'):
        if update['function'] == func:
            for field in update.get('fields', []):
                if field[0] not in values:
                    values[field[0]] = field[1]

    return values


@bp.route(f'{url_prefix}/reload', methods=['GET'])
def reload_actions():
    """
    Reload actions file.

    :return: redirect or response
    """
    from json.decoder import JSONDecodeError
    from jsonschema import ValidationError
    try:
        _load_actions_file()
        return redirect_or_response(200)
    except (ValidationError, JSONDecodeError) as e:
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

    :exception jsonschema.ValidationError: If validation check fails
    :exception json.decoder.JSONDecodeError: If json.load fails
    """
    actions.clear()
    create_empty_actions_file()
    with open(get_actions_file(), 'r') as f:
        from json import load
        content: dict = load(f)

    validate(instance=content, schema=actions_schema)

    for file_def in content:
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
    from jsonschema import ValidationError
    try:
        _load_actions_file()
    except (ValidationError, JSONDecodeError) as e:
        flash("Syntax or decoding error: " + str(e))
        actions = {}
    return actions


def set_actions_file(filepath: str):
    """
    Set a new actions filepath to plugins actions_file config value.

    :param filepath: full qualified filepath
    """
    config.set(name, 'actions_file', filepath)
