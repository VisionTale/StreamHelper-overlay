from flask import request, flash, render_template
from os.path import join

from webapi.libs.api.response import redirect_or_response
from webapi.libs.api.parsing import param, is_set
from webapi.libs.text import camel_case

from .. import bp, config, name, logger, settings_folder
from .rundown import add_to_current_rundown, remove_from_current_rundown

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
    param('uuid')
    if not is_set(uuid):
        return redirect_or_response(400, 'Missing parameter uuid')

    remove_from_current_rundown(uuid)
    return redirect_or_response(200, 'Success')


@bp.route(f'{url_prefix}/show', methods=['GET', 'POST'])
def show_definition():
    values = request.args.to_dict() or request.form.to_dict()
    definition = param('filename')
    if not is_set(definition):
        return redirect_or_response(400, 'Missing parameter filename')

    return render_template(f'overlays/{definition}', **values)


@bp.route(f'{url_prefix}/reload', methods=['GET'])
def reload_definitions():
    try:
        _load_definitions_file()
        return redirect_or_response(200)
    except SyntaxError as e:
        return redirect_or_response(400, e.msg)


@bp.route(f'{url_prefix}/save_content', methods=['POST'])
def save_definitions_content():
    from urllib.parse import unquote
    content = unquote(request.form.get('content'))
    with open(get_definitions_file(), 'w') as f:
        f.write(content)
    return redirect_or_response(200)


def create_kwargs(definition_name: str, r: request) -> dict:
    kwargs = dict()
    for d in getattr(definitions, definition_name):
        kwargs[d[0]] = r.args.get(d[0], d[1], d[2])
    return kwargs


def _load_definitions_file():
    definitions.clear()
    from json import load
    with open(get_definitions_file(), 'r') as f:
        content: dict = load(f)
    if not type(content) == dict:
        raise SyntaxError('Content is not a json object')
    for file_def in content:
        if not type(content[file_def]) == dict:
            raise SyntaxError(f'Content of {file_def} is not a valid json array')
        if 'filename' not in content[file_def].keys() or type(content[file_def]['filename']) != str:
            raise SyntaxError(f'Content of {file_def} misses the filename attribute')
        if 'fields' not in content[file_def].keys() or type(content[file_def]['fields']) != list:
            raise SyntaxError(f'Content of {file_def} misses the fields attribute')
        if 'display_name' not in content[file_def].keys():
            content[file_def]['display_name'] = camel_case(file_def, '_')
        definitions[file_def] = content[file_def]


def get_definitions_file() -> str:
    """
    Get the current definitions filepath from plugins definitions_file config value.

    :return: full qualified filepath
    """
    return config.get_or_set(name,
                             'definitions_file',
                             join(settings_folder, 'definitions.json')
                             )


def get_definitions() -> dict:
    """
    Reloads and returns all definitions from the file returned by get_definitions_file()

    :return: dict of definitions
    """
    global definitions
    try:
        _load_definitions_file()
    except SyntaxError as e:
        flash("Syntax error: " + str(e))
        definitions = {}
    return definitions


def set_definitions_file(filepath: str):
    """
    Set a new definitions filepath to plugins definitions_file config value.

    :param filepath: full qualified filepath
    """
    config.set(name, 'definitions_file', filepath)
