from urllib.parse import quote

from flask import request

from . import bp
from .libs import connector
from webapi.libs.data_structures import inverse_stack


@bp.route('/ping', methods=['GET'])
def ping():  # TODO Use to show if overlay server is running
    return '', 200


@bp.route('/play_html', methods=['GET'])
def play_html():

    form = request.args.to_dict()
    route = form.pop('route')
    channel = form.pop('channel')
    layer = form.pop('layer')

    from . import name, config
    overlay_server = config.get(name, 'overlay_server')
    if not overlay_server.endswith('/'):
        overlay_server += '/'

    stack = inverse_stack(form, 'popitem')
    params = "&".join("%s=%s" % (quote(k.strip()), quote(v.strip())) for k, v in stack)

    command = f'PLAY {channel}-{layer} [HTML] "{overlay_server}{route}?{params}"'

    server, port = config.get(name, 'server').split(':')

    http_response_code = execute_command(server, port, command)
    return '', http_response_code


@bp.route('/clear', methods=['GET'])
def clear():

    form = request.args.to_dict()
    channel = form.pop('channel')
    layer = form.pop('layer')

    from . import name, config
    overlay_server = config.get(name, 'overlay_server')
    if not overlay_server.endswith('/'):
        overlay_server += '/'

    command = f'CLEAR {channel}-{layer}'

    server, port = config.get(name, 'server').split(':')

    http_response_code = execute_command(server, port, command)
    return '', http_response_code


def execute_command(server, port, command) -> int:
    from . import logger
    logger.debug(f'Invoked socket command to {server}:{port} "{command}"')
    http_response_code = 200
    try:
        connector.init(server, int(port))
        connector.send_command(command)
    except OSError as e:
        http_response_code = 500
        logger.warning(f"Client execution failed: {e}")
    finally:
        connector.close()
    return http_response_code
