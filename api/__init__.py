"""
Basic overlay api setup.
"""

api_prefix: str = '/api'

from webapi.libs.api.response import response

from .. import bp
from . import caspar


@bp.route(f'{api_prefix}/ping', methods=['GET'])
def ping():
    """
    Returns an empty 200 response.

    :return: 200 response
    """
    return response(200)
