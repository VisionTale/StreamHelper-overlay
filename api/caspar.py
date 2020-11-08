from flask import request
from urllib.parse import quote

from webapi.libs.api.response import response
from webapi.libs.data_structures import inverse_stack

from . import api_prefix

from .. import bp, config, name, logger
from ..libs.caspar import connector

caspar_prefix: str = f'{api_prefix}/caspar'


@bp.route('/play_html', methods=['GET'])
def play_html():
    form = request.args.to_dict()
    route = form.pop('route')
    channel = form.pop('channel')
    layer = form.pop('layer')

    overlay_server = config.get(name, 'overlay_server')
    if not overlay_server.endswith('/'):
        overlay_server += '/'

    stack = inverse_stack(form, 'popitem')
    params = "&".join("%s=%s" % (quote(k.strip()), quote(v.strip())) for k, v in stack)

    command = f'PLAY {channel}-{layer} [HTML] "{overlay_server}{route}?{params}"'

    server, port = config.get(name, 'server').split(':')

    http_response_code = execute_command(server, port, command)
    return response(request, http_response_code)


@bp.route('/clear', methods=['GET'])
def clear():
    form = request.args.to_dict()
    channel = form.pop('channel')
    layer = form.pop('layer')

    overlay_server = config.get(name, 'overlay_server')
    if not overlay_server.endswith('/'):
        overlay_server += '/'

    command = f'CLEAR {channel}-{layer}'

    server, port = config.get(name, 'server').split(':')

    http_response_code = execute_command(server, port, command)
    return response(request, http_response_code)


def execute_command(server, port, command) -> int:
    logger.debug(f'Invoked socket command to {server}:{port} "{command}"')
    response_code = 200
    try:
        connector.init(server, int(port))
        connector.send_command(command)
    except OSError as e:
        response_code = 500
        logger.warning(f"Client execution failed: {e}")
    finally:
        connector.close()
    return response_code
