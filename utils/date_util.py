from datetime import date, timedelta, datetime

DAY_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DAY_FORMAT = '%Y-%m-%d'
DAY_DENSE_FORMAT = '%Y%m%d'


def today():
    return datetime.now()


def to_str(_time: datetime | date, _format: str):
    return _time.strftime(_format)


def today_str():
    return to_str(today(), DAY_FORMAT)


def today_str_dense():
    return to_str(today(), DAY_DENSE_FORMAT)


def current_time():
    return datetime.now()


def current_time_str():
    return to_str(current_time(), DAY_TIME_FORMAT)


def today_time_str():
    return to_str(date.today(), DAY_TIME_FORMAT)


def day_to_time(day_str):
    _time = datetime.strptime(day_str, DAY_FORMAT)
    return to_str(_time, DAY_TIME_FORMAT)


def day_sub(day_time_str, day):
    _time = datetime.strptime(day_time_str, DAY_TIME_FORMAT)
    _time = _time + timedelta(days=day)
    return to_str(_time, DAY_TIME_FORMAT)


if __name__ == '__main__':
    print(today_str())
    print(current_time_str())
    print(today_time_str())
    print(day_sub(today_time_str(), -7))
    print(day_to_time(today_str()))
