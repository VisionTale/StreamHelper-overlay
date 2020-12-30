"""
Settings routes for the overlay plugin.
"""
from flask import request

from .. import bp, config, name
from webapi.libs.api.response import redirect_or_response
from webapi.libs.api.parsing import param, is_set

settings_prefix: str = "/settings"


@bp.route(f'{settings_prefix}/toggle_caspar', methods=['GET', 'POST'])
def toggle_caspar():
    """
    Toggles caspar activation (only affects interface).

    :return: redirect or response
    """
    from distutils.dist import strtobool
    state: bool = bool(strtobool(config.get(name, 'use_caspar'))) ^ True
    config.set(name, 'use_caspar', str(state).lower())

    return redirect_or_response(200, 'Success')


@bp.route(f'{settings_prefix}/set_caspar_server_url', methods=['GET', 'POST'])
def set_caspar_server_url():
    """
    Set the url of the caspar server to call to.

    Arguments:
            - url

    :return: redirect or response
    """
    server = param('url')
    if not is_set(server):
        return redirect_or_response(400, 'Missing parameter url')
    config.set(name, 'caspar_server', server)
    return redirect_or_response(200, 'Success')


@bp.route(f'{settings_prefix}/set_overlay_server_url', methods=['GET', 'POST'])
def set_overlay_server_url():
    """
    Set the url the remote server is supposed to call back. This is mainly intended to use the interface via a different
    network interface, e.g. access this server via localhost but the caspar server is remote. It theoretically can
    also be used to set a different server if it has the same configuration.

    Arguments:
        - url

    :return: redirect or response
    """
    server = param('url')
    if not is_set(server):
        return redirect_or_response(400, 'Missing parameter url')
    config.set(name, 'overlay_server', server)
    return redirect_or_response(200, 'Success')


@bp.route(f'{settings_prefix}/set_current_rundown', methods=['GET', 'POST'])
def set_current_rundown():
    """
    Set the current rundown.

    :return: redirect or response
    """
    rundown = param('name')
    if not is_set(rundown):
        return redirect_or_response(400, 'Missing parameter name')
    config.set(name, 'current_rundown', rundown)
    return redirect_or_response(200, 'Success')
