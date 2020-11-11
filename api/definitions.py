from flask import request
from os.path import join

from webapi.libs.api.response import redirect_or_response

from .. import bp, config, name, logger
from . import api_prefix

definition_prefix: str = f'{api_prefix}/definitions'
active_definitions: list = []
definitions: list = []


@bp.route(f'{definition_prefix}/add', methods=['GET'])
def add_definition():

    definition = request.args.get('definition')
    if not definition or definition == '':
        return redirect_or_response(request, 400, 'Missing parameter "definition"')

    active_definitions.append(definition)
    _save()


@bp.route(f'{definition_prefix}/remove', methods=['GET'])
def remove_definition():
    definition = request.args.get('definition')
    if not definition or definition == '':
        return redirect_or_response(request, 400, 'Missing parameter "definition"')

    active_definitions.append(definition)
    _save()


@bp.route(f'{definition_prefix}/show', methods=['GET'])
def show_definition():
    definition = request.args.get('definition')
    if not definition or definition == '':
        return redirect_or_response(request, 400, 'Missing parameter "definition"')


@bp.route(f'{definition_prefix}/reload', methods=['GET'])
def reload_definitions():
    try:
        _load_definitions_file()
        return redirect_or_response(request, 200)
    except SyntaxError as e:
        return redirect_or_response(request, 400, e.msg)


@bp.route(f'{definition_prefix}/save_content', methods=['POST'])
def save_definitions_content():
    from urllib.parse import unquote
    content = unquote(request.form.get('content'))
    with open(get_definitions_file(), 'w') as f:
        f.write(content)
    return redirect_or_response(request, 200)


def create_routes():
    for d in dir(definitions):
        if not d.endswith('_definition'):
            continue
        def_name = d.replace('_definition', '')

        exec(
            f'''
@bp.route('{definition_prefix}/display/{def_name}', methods=['GET'])
def {def_name}():
    kwargs = create_kwargs("{d}", request)
    return render_template('{def_name}.html', **kwargs)
'''
        )


def create_kwargs(definition_name: str, r: request) -> dict:
    kwargs = dict()
    for d in getattr(definitions, definition_name):
        kwargs[d[0]] = r.args.get(d[0], d[1], d[2])
    return kwargs


def _save():
    config.set(name, 'active_definitions', ', '.join(active_definitions))


def _load():
    global active_definitions
    active_definitions = config.get_or_set(name, 'active_definitions', '').split(', ')


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
        if 'filename' not in content.keys() or type(content[file_def]['filename']) != str:
            raise SyntaxError(f'Content of {file_def} misses the filename attribute')
        if 'fields' not in content.keys() or type(content[file_def]['fields']) != list:
            raise SyntaxError(f'Content of {file_def} misses the fields attribute')
        definitions[file_def] = content[file_def]


def get_definitions_file() -> str:
    return config.get_or_set(name, 'definitions_file', join(config.get('webapi', 'data_dir'), 'definitions.json'))


def set_definitions_file(filepath: str):
    config.set(name, 'definitions_file', filepath)
