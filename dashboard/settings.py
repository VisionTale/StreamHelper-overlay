from flask import request
from webapi.libs.api.response import redirect_or_response

from .. import bp, config, name


settings_prefix: str = "/settings"


@bp.route(f'{settings_prefix}/activate_caspar')
def activate_caspar():
    config.set(name, 'use_caspar', 'true')
    return redirect_or_response(request, 200, 'Success')


@bp.route(f'{settings_prefix}/deactivate_caspar')
def deactivate_caspar():
    config.set(name, 'use_caspar', 'false')
    return redirect_or_response(request, 200, 'Success')


@bp.route(f'{settings_prefix}/set_caspar_server_url')
def set_caspar_server_url():
    server = request.args.get('url')
    if not server or server == '':
        return redirect_or_response(request, 400, 'Missing parameter url')
    config.set(name, 'caspar_server', server)
    return redirect_or_response(request, 200, 'Success')


@bp.route(f'{settings_prefix}/set_overlay_server_url')
def set_overlay_server_url():
    server = request.args.get('url')
    if not server or server == '':
        return redirect_or_response(request, 400, 'Missing parameter url')
    config.set(name, 'overlay_server', server)
    return redirect_or_response(request, 200, 'Success')


@bp.route(f'{settings_prefix}/set_current_rundown')
def set_current_rundown():
    rundown = request.args.get('name')
    if not rundown or rundown == '':
        return redirect_or_response(request, 400, 'Missing parameter name')
    config.set(name, 'current_rundown', rundown)
    return redirect_or_response(request, 200, 'Success')

