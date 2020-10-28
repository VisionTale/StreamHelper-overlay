from flask import render_template, request
from . import bp, definitions


def create_routes():
    for d in dir(definitions):
        if not d.endswith('_definition'):
            continue
        name = d.replace('_definition', '')

        exec(
            f'''
@bp.route('/{name}', methods=['GET'])
def {name}():
    kwargs = create_kwargs("{d}", request)
    return render_template('{name}.html', **kwargs)
'''
        )


def create_kwargs(definition_name: str, r: request) -> dict:
    kwargs = dict()
    for d in getattr(definitions, definition_name):
        kwargs[d[0]] = r.args.get(d[0], d[1], d[2])
    return kwargs
