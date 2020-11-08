from amcp_pylib.core import Client
from amcp_pylib.module.query import BYE

from . import connector


def is_caspar_up(server, port) -> bool:
    """
    Checks if CasparCG server is up and reachable.
    :param server: server name (domain or ip)
    :param port: port if caspar server
    :return: bool
    """
    try:
        client = Client()
        client.connect(server, port)
        client.send(BYE())
        del client
        return True
    except OSError:
        return False
