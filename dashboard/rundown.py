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
    Saves a value key pair for a definition.

    Arguments:
        - uuid, used to identify definition
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
    Saves a value key pair for a definition.

    Arguments:
        - definition
        - key
        - value (optional, uses empty string as fallback)

    :return: redirect or 200 response
    """
    definition = param('definition')
    if not is_set(definition):
        return redirect_or_response(400, 'Missing parameter definition')
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


@bp.route(f'{url_prefix}/run', methods=['GET', 'POST'])
def definition_exec():
    """
    Execute a definition within a rundown. The definition will be executed based on the active services.

    The currently active rundown must not be empty.

    Arguments:
        - service [caspar,]
        - action [start, stop,]
        - uuid, used to identify definition. Must belong to current rundown.
        - rundown, to read settings from. Falls back to current rundown if not set.

    :return: redirect or response
    """
    service = param('service')
    if not is_set(service):
        return redirect_or_response(400, 'Missing parameter service')
    uuid = param('uuid')
    if not is_set(uuid):
        return redirect_or_response(400, 'Missing parameter uuid')
    action = param('action')
    if not is_set(action):
        return redirect_or_response(400, 'Missing parameter action')
    current_rundown = param('rundown') or get_current_rundown_name()
    if not is_set(current_rundown):
        return redirect_or_response(400, 'No rundown selected')
    rundown = rundowns[current_rundown]['rundown']

    for d in rundown:
        if d['id'] == uuid:
            if service.lower().startswith('caspar'):
                return _definition_exec_caspar(action, d)
            else:
                return redirect_or_response(400, 'Overlay service unknown')
    return redirect_or_response(400, 'No valid definition found')


def _definition_exec_caspar(action: str, definition: dict):
    rundown = get_current_rundown()
    groups = rundown.get('global', {})
    values = {**definition['values']}
    for group in groups:
        values: dict = {**values, **groups[group]}
    values.setdefault('channel', 1)
    values.setdefault('layer', 7)
    values.setdefault('transition', 'MIX')
    values.setdefault('hold', 0)
    values.setdefault('fadein', 1000)
    values.setdefault('fadeout', 1000)

    values['type'] = 'definition'

    from .definitions import get_definitions
    definitions = get_definitions()
    values['filename'] = definitions[definition['name']]['filename']
    for d in definitions:
        for field in definitions[d].pop('fields', []):
            if field[0] not in values:
                values[field[0]] = str(field[1])
        for group in definitions[d].pop('groups', {}):
            for field in group.get('fields', []):
                if field[0] not in values:
                    values[field[0]] = str(field[1])

    from requests import get
    if action == 'html':
        get(f"{request.url_root}/{url_for(name+'.caspar_play_html')}", params=values)
    elif action == 'stop':
        values['javascript'] = 'fadeout()'
        get(f"{request.url_root}/{url_for(name+'.caspar_call')}", params=values)
    elif action == 'clear':
        get(f"{request.url_root}/{url_for(name+'.caspar_clear')}", params=values)
    else:
        return redirect_or_response(400)

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


def add_to_current_rundown(definition_name: str):
    """
    Add a definition to the current rundown.

    :param definition_name: name of the definition
    :exception AttributeError: If current rundown is not set.
    """
    current_rundown = get_current_rundown_name()
    if not is_set(current_rundown):
        raise AttributeError('No rundown selected')

    from .definitions import get_definitions
    definitions = get_definitions()
    if definition_name not in definitions.keys():
        raise AttributeError('Invalid definition selected')

    definition_container = {
        'name': definition_name,
        'display_name': camel_case(definition_name, '_'),
        'id': str(uuid4()),
        'pos': 0,
        'values': {}
    }
    if 'groups' in definitions.keys():
        for group in definitions['groups']:
            if group.get('area', 'local') == 'global':
                if 'fields' in group.keys():
                    for field in group['fields']:
                        definition_container[field[0]] = str(field[1])
    rundowns[current_rundown]['rundown'].append(definition_container)

    _renumbering_current_rundown()
    _save_rundowns()


def remove_from_current_rundown(uuid: str):
    """
    Remove a definition from the current rundown.

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
