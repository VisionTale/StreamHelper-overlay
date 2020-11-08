api_prefix: str = '/api'

from .. import bp

from . import caspar, definitions


@bp.route(f'{api_prefix}/ping', methods=['GET'])
def ping():
    return "", 200

