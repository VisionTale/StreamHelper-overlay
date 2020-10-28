def to_date(date_str: str):
    """
    Helper function transforming a string to a date
    :param date_str: date as string of format YYYY-mm-dd
    :return: datetime object
    """
    from datetime import datetime
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def to_date_time(date_str: str):
    """
    Helper function transforming a string to a date
    :param date_str: date as string of format YYYY-mm-dd HH:MM:SS
    :return: datetime object
    """
    from datetime import datetime
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
