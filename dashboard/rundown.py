from os.path import join, isfile
from json import load, dump
from uuid import uuid4
from typing import List

from flask import request, flash, url_for

from webapi.libs.api.response import redirect_or_response
from webapi.libs.api.parsing import param, is_set
from webapi.libs.system import create_underlying_folder
from webapi.libs.text import camel_case

from .. import bp, name, config, logger, settings_folder

url_prefix: str = '/rundown'
rundowns = dict()


@bp.route(f'{url_prefix}/add', methods=['GET', 'POST'])
def add_rundown():
    """
    Add a new rundown.

    Arguments:
        - name
        - display_name (optional, uses name as fallback)

    :return: redirect or 200 response
    """
    rundown_name: str = param('name')
    if not is_set(rundown_name):
        return redirect_or_response(400, 'Missing parameter name')
    display_name: str = param('display_name', rundown_name)

    rundowns[rundown_name] = {
        'display_name': display_name,
        'rundown': [],
        'global': {}
    }

    _save_rundowns()

    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/remove', methods=['GET', 'POST'])
def remove_rundown():
    """
    Removes a rundown.

    Arguments:
        - name

    :return: redirect or 200 response
    """
    rundown_name: str = param('name')
    if not is_set(rundown_name):
        return redirect_or_response(400, 'Missing parameter name')

    del rundowns[rundown_name]

    _save_rundowns()

    if config.get(name, 'current_rundown') == rundown_name:
        config.set(name, 'current_rundown', '')

    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/save_value', methods=['GET', 'POST'])
def save_value():
    """
    Saves a value key pair for a action.

    Arguments:
        - uuid, used to identify action
        - key
        - value (optional, uses empty string as fallback)

    :return: redirect or 200 response
    """
    uuid = param('uuid')
    if not is_set(uuid):
        return redirect_or_response(400, 'Missing parameter uuid')
    key = param('key')
    if not is_set(key):
        return redirect_or_response(400, 'Missing parameter key')
    value = param('value', '')

    current_rundown = get_current_rundown()
    for run in current_rundown['rundown']:
        if run['id'] == uuid:
            run['values'][key] = value

    _save_rundowns()

    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/save_global_value', methods=['GET', 'POST'])
def save_global_value():
    """
    Saves a value key pair for a action.

    Arguments:
        - action
        - key
        - group
        - value (optional, uses empty string as fallback)

    :return: redirect or 200 response
    """
    action = param('action')
    if not is_set(action):
        return redirect_or_response(400, 'Missing parameter action')
    key = param('key')
    if not is_set(key):
        return redirect_or_response(400, 'Missing parameter key')
    group = param('group')
    if not is_set(group):
        return redirect_or_response(400, 'Missing parameter group')
    value = param('value', '')

    current_rundown = get_current_rundown()
    if group not in current_rundown['global']:
        current_rundown['global'][group] = dict()
    current_rundown['global'][group][key] = value

    _save_rundowns()

    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/save_update_value', methods=['GET', 'POST'])
def save_update_value():
    """
    Saves a value key pair for a action.

    Arguments:
        - uuid, used to identify action
        - func, update function
        - key
        - value (optional, uses empty string as fallback)

    :return: redirect or 200 response
    """
    uuid = param('uuid')
    if not is_set(uuid):
        return redirect_or_response(400, 'Missing parameter uuid')
    func = param('func')
    if not is_set(func):
        return redirect_or_response(400, 'Missing parameter func')
    key = param('key')
    if not is_set(key):
        return redirect_or_response(400, 'Missing parameter key')
    value = param('value', '')

    current_rundown = get_current_rundown()
    for run in current_rundown['rundown']:
        if run['id'] == uuid:
            if 'updates' not in run:
                run['updates'] = dict()
            if func not in run['updates']:
                run['updates'][func] = dict()
            run['updates'][func][key] = value

    _save_rundowns()

    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/run', methods=['GET', 'POST'])
def action_exec():
    """
    Execute a action within a rundown.

    The currently active rundown must not be empty.

    Arguments:
        - service [caspar,]
        - event, type of event [html, stop, clear,]
        - rundown, name of rundown
        - action, unique id of action

    :return: redirect or response
    """
    service = param('service')
    if not is_set(service):
        return redirect_or_response(400, 'Missing parameter service')
    event = param('event')
    if not is_set(event):
        return redirect_or_response(400, 'Missing parameter event')
    rundown = param('rundown')
    if not is_set(rundown):
        return redirect_or_response(400, 'Missing parameter rundown')
    action = param('action')
    if not is_set(action):
        return redirect_or_response(400, 'Missing parameter action')

    if service.lower().startswith('caspar'):
        return _action_exec_caspar(event, rundown, action)
    else:
        return redirect_or_response(400, 'Overlay service unknown')


def _action_exec_caspar(event: str, rundown: str, action: str):
    from requests import get
    # TODO Variable setting
    channel = "1"
    layer = "7"
    additional = ""
    if event == 'html':
        get(f"{request.url_root}/{url_for(name+'.caspar_play_html')}",
            params={"rundown": rundown, "action": action, "channel": channel, "layer": layer, "additional": additional})
    elif event == 'stop':
        get(f"{request.url_root}/{url_for(name+'.caspar_call')}",
            params={"rundown": rundown, "action": action, "channel": channel, "layer": layer, "function": "fadeout"})
    elif event == 'clear':
        get(f"{request.url_root}/{url_for(name+'.caspar_clear')}", params={"rundown": rundown, "action": action})
    elif event == 'update':
        func = param('func')
        if not is_set(func):
            return redirect_or_response(400, 'Missing parameter func for event "update"')
        get(f"{request.url_root}/{url_for(name + '.caspar_call')}",
            params={"rundown": rundown, "action": action, "channel": channel, "layer": layer, "function": func})
    else:
        return redirect_or_response(400, 'No valid event')

    return redirect_or_response(200, 'Success')


def list_rundowns() -> List[str]:
    """
    Returns all rundown names.

    :return: list of rundowns
    """
    return rundowns.keys()


def get_rundowns() -> dict:
    """
    Return all rundowns.

    :return: dictionary with rundowns, a rundown is accessed via its name
    """
    return rundowns


def _save_rundowns():
    """
    Save rundowns from memory to file specified via get_rundown_file().
    """
    with open(get_rundown_file(), 'w') as f:
        dump(rundowns, f)


def load_rundowns():
    """
    Loads data from rundown file.
    """
    global rundowns
    file = get_rundown_file()
    if not isfile(file):
        create_underlying_folder(file)
        rundowns = {}
        with open(file, 'w') as f:
            dump(rundowns, f)
    else:
        with open(file, 'r') as f:
            rundowns = load(f)
            for rundown in rundowns:
                rundowns[rundown]['rundown'].sort(key=_sort_rundown_key)


def get_rundown_file():
    """
    Get the filepath to store rundown configurations.

    :return: filepath
    """
    return config.get_or_set(name, 'rundown_file', join(settings_folder, 'rundown.json'))


def set_rundown_file(filepath):
    """
    Set a new filepath to save the rundown configurations.

    :param filepath: filepath to save the file to
    :return:
    """
    return config.set(name, 'rundown_file', filepath)


def get_current_rundown_name() -> str:
    """
    Returns the name of the current rundown. If the name is set and corresponds to no rundown, the name is reset.

    :return: name of the current rundown
    """
    current_rundown = config.get_or_set(name, 'current_rundown', '')
    if current_rundown != '' and current_rundown not in rundowns:
        current_rundown = ''
        config.set(name, 'current_rundown', '')
    return current_rundown


def get_current_rundown() -> dict:
    """
    Returns the current rundown. None if not set.

    :return: rundown object
    """
    current_rundown = get_current_rundown_name()
    return rundowns[current_rundown] if current_rundown != '' else None


def add_to_current_rundown(action_name: str):
    """
    Add a action to the current rundown.

    :param action_name: name of the action
    :exception AttributeError: If current rundown is not set.
    """
    current_rundown = get_current_rundown_name()
    if not is_set(current_rundown):
        raise AttributeError('No rundown selected')

    from .actions import get_actions
    actions = get_actions()
    if action_name not in actions.keys():
        raise AttributeError('Invalid action selected')

    action_container = {
        'name': action_name,
        'display_name': camel_case(action_name, '_'),
        'id': str(uuid4()),
        'pos': 0,
        'values': {}
    }
    if 'groups' in actions.keys():
        for group in actions['groups']:
            if group.get('area', 'local') == 'global':
                if 'fields' in group.keys():
                    for field in group['fields']:
                        action_container[field[0]] = str(field[1])
    rundowns[current_rundown]['rundown'].append(action_container)

    _renumbering_current_rundown()
    _save_rundowns()


def remove_from_current_rundown(uuid: str):
    """
    Remove a action from the current rundown.

    :param uuid: uuid saved in the rundown
    :exception AttributeError: If current rundown is not set.
    """
    current_rundown = get_current_rundown_name()
    if not is_set(current_rundown):
        raise AttributeError('No rundown selected')

    rundown = rundowns[current_rundown]['rundown']
    for i in range(len(rundown)):
        if rundown[i]['id'] == uuid:
            del rundown[i]
            break
    _renumbering_current_rundown()
    _save_rundowns()


def rename_in_current_rundown(uuid: str, new_name: str):
    """
    Rename a action in the current rundown.

    :param uuid: uuid saved in the rundown
    :param new_name: new display name
    :exception AttributeError: If current rundown is not set.
    """
    current_rundown = get_current_rundown_name()
    if not is_set(current_rundown):
        raise AttributeError('No rundown selected')

    rundown = rundowns[current_rundown]['rundown']
    for i in range(len(rundown)):
        if rundown[i]['id'] == uuid:
            rundown[i]['display_name'] = new_name
            break

    _save_rundowns()


def _renumbering_current_rundown():
    """
    Set the position attribute of all rundowns based on their position in the rundown list. Used for sorting after
    reload.

    :exception AttributeError: If current rundown is not set.
    """
    current_rundown = get_current_rundown_name()
    if not is_set(current_rundown):
        raise AttributeError('No rundown selected')

    rundown = rundowns[current_rundown]['rundown']
    for i in range(len(rundown)):
        rundown[i]['pos'] = i


def _sort_rundown_key(rundown):
    """
    Key to sort rundowns. Sorted by value of pos attribute.

    :param rundown: rundown to check for
    :return: position attribute
    """
    return rundown['pos']
