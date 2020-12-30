from flask import request, url_for
from urllib.parse import quote
from typing import Tuple

from webapi.libs.api.response import response, redirect_or_response
from webapi.libs.data_structures import inverse_stack
from webapi.libs.api.parsing import is_set, param

from . import api_prefix

from .. import bp, config, name, logger
from ..libs.caspar import connector

caspar_prefix: str = f'{api_prefix}/caspar'


@bp.route(f'{caspar_prefix}/play_html', methods=['GET', 'POST'])
def caspar_play_html():
    """
    Call CasparCG server to play a html site from this server.

    Arguments:
        - rundown, name of the rundown
        - action, uuid of the action that stores all values
        - channel, casparcg channel
        - layer, casparcg layer
        - additional, additional arguments to casparcg (defaults to be empty)

    :return: http response code
    """

    rundown = param('rundown')
    if not is_set(rundown):
        return redirect_or_response(400, 'Missing parameter rundown')
    action = param('action')
    if not is_set(action):
        return redirect_or_response(400, 'Missing parameter action')
    channel = param('channel')
    if not is_set(channel):
        return redirect_or_response(400, 'Missing parameter channel')
    layer = param('layer')
    if not is_set(layer):
        return redirect_or_response(400, 'Missing parameter layer')
    additional = param('additional', "")

    overlay_server = _get_overlay_server()
    recall_url = f'{overlay_server}{url_for(f"{name}.show_action")}?rundown={rundown}&action={action}'

    command = f'PLAY {channel}-{layer} [HTML] "{recall_url}" {additional}'

    server, port = _get_server_and_port()

    http_response_code = _execute_command(server, port, command)
    return response(http_response_code)


@bp.route(f'{caspar_prefix}/call', methods=['GET', 'POST'])
def caspar_call():
    channel = param('channel')
    if not is_set(channel):
        return redirect_or_response(400, 'Missing parameter channel')
    layer = param('layer')
    if not is_set(layer):
        return redirect_or_response(400, 'Missing parameter layer')
    javascript = param('function')
    if not is_set(javascript):
        return redirect_or_response(400, 'Missing parameter function')

    command = f'CALL {channel}-{layer} {javascript}'

    server, port = _get_server_and_port()

    http_response_code = _execute_command(server, port, command)
    return response(http_response_code)


@bp.route(f'{caspar_prefix}/clear', methods=['GET', 'POST'])
def caspar_clear():
    channel = param('channel')
    if not is_set(channel):
        return redirect_or_response(400, 'Missing parameter channel')
    layer = param('layer')
    if not is_set(layer):
        return redirect_or_response(400, 'Missing parameter layer')

    command = f'CLEAR {channel}-{layer}'

    server, port = _get_server_and_port()

    http_response_code = _execute_command(server, port, command)
    return response(http_response_code)


def _execute_command(server, port, command) -> int:
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


def _get_server_and_port() -> Tuple[str, str]:
    return config.get(name, 'caspar_server').split(':')


def _get_overlay_server() -> str:
    overlay_server = config.get(name, 'overlay_server')
    if not overlay_server.endswith('/'):
        overlay_server += '/'
        config.set(name, 'overlay_server', overlay_server)
    return overlay_server
