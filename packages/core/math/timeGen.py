import datetime


def get_date_time():
    return datetime.datetime.now().isoformat(timespec='seconds').replace(':', '_').replace('.', '_')


def get_date():
    return datetime.datetime.now().strftime("%Y_%m_%d")