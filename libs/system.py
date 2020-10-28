def is_up(host) -> bool:
    """
    Check if a host is up and running.
    :param host: hostname
    :return: whether the host is reachable
    """
    from os import system
    return True if system("ping -c 1 " + host + ' > /dev/null 2>&1') == 0 else False
