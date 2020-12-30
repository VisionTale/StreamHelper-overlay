from flask import request, flash, render_template

from webapi.libs.api.response import redirect_or_response
from webapi.libs.api.parsing import param, is_set
from webapi.libs.text import camel_case

from .. import bp, config, name, logger, settings_folder
from .rundown import add_to_current_rundown, remove_from_current_rundown, rename_in_current_rundown

url_prefix: str = '/definitions'
definitions: dict = {}


@bp.route(f'{url_prefix}/add', methods=['GET', 'POST'])
def add_definition():
    """
    Add a definition to the current rundown. A UUID will be assigned to the definition.

    Arguments:
        - uuid

    :return: redirect or response
    """

    definition = param('name')
    if not is_set(definition):
        return redirect_or_response(400, 'Missing parameter name')

    try:
        add_to_current_rundown(definition)
    except AttributeError as e:
        return redirect_or_response(400, e.msg)

    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/remove', methods=['GET', 'POST'])
def remove_definition():
    """
    Remove a definition from the current rundown based on it's uuid.

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
def rename_definition():
    """
    Rename a definition from the current rundown based on it's uuid.

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
def show_definition():
    """
    Rendered template file.

    All arguments except of the filename argumeent are passed to the file.

    Arguments:
        - filename

    :return: rendered file
    """
    values: dict = request.args.to_dict() or request.form.to_dict()
    definition = values.pop('filename', '')
    if not is_set(definition):
        return response(400, 'Missing parameter filename', graphical=True)
    from os.path import isfile, join
    if not isfile(join(bp.template_folder, 'overlays', definition)):
        return response(404, 'Definition file not found', graphical=True)

    return render_template(f'overlays/{definition}', **values)


@bp.route(f'{url_prefix}/reload', methods=['GET'])
def reload_definitions():
    """
    Reload definitions file.

    :return: redirect or response
    """
    from json.decoder import JSONDecodeError
    try:
        _load_definitions_file()
        return redirect_or_response(200)
    except (SyntaxError, JSONDecodeError) as e:
        return redirect_or_response(400, e.msg)


@bp.route(f'{url_prefix}/save_content', methods=['POST'])
def save_definitions_file_content():
    """
    Save file content of definitions.json.

    Arguments:
        - content, encoded file content

    :return: redirect or response
    """
    from urllib.parse import unquote
    content = unquote(request.form.get('content'))

    create_empty_definitions_file()
    with open(get_definitions_file(), 'w') as f:
        f.write(content)

    return redirect_or_response(200)


def _load_definitions_file():
    """
    Load the definitions file.

    :exception SyntaxError: If validation check fails
    :exception json.decoder.JSONDecodeError: If json.load fails
    """
    definitions.clear()
    create_empty_definitions_file()
    with open(get_definitions_file(), 'r') as f:
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
        definitions[file_def] = content[file_def]


def get_definitions_file() -> str:
    """
    Get the current definitions filepath from plugins definitions_file config value.

    :return: full qualified filepath
    """
    from os.path import join
    return config.get_or_set(name,
                             'definitions_file',
                             join(settings_folder, 'definitions.json')
                             )


def create_empty_definitions_file():
    """
    Creates the file (and the corresponding folder) for the definitions.

    :return:
    """
    from os.path import dirname, isdir, isfile
    if not isdir(dirname(get_definitions_file())):
        from pathlib import Path
        Path(dirname(get_definitions_file())).mkdir(parents=True)
    if not isfile(get_definitions_file()):
        from json import dump
        with open(get_definitions_file(), 'w') as f:
            dump({}, f)


def get_definitions() -> dict:
    """
    Reloads and returns all definitions from the file returned by get_definitions_file()

    :return: dict of definitions
    """
    global definitions
    from json.decoder import JSONDecodeError
    try:
        _load_definitions_file()
    except (SyntaxError, JSONDecodeError) as e:
        flash("Syntax or decoding error: " + str(e))
        definitions = {}
    return definitions


def set_definitions_file(filepath: str):
    """
    Set a new definitions filepath to plugins definitions_file config value.

    :param filepath: full qualified filepath
    """
    config.set(name, 'definitions_file', filepath)
