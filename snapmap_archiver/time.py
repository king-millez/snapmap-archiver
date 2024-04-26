from datetime import datetime


def since_epoch(since_time: str) -> int:
    if since_time.isdigit():
        return int(since_time)

    num = int(since_time[:-1])
    if since_time[-1] == "m":
        return int(datetime.now().timestamp()) - num * 60
    if since_time[-1] == "h":
        return int(datetime.now().timestamp()) - num * 60 * 60
    if since_time[-1] == "d":
        return int(datetime.now().timestamp()) - num * 60 * 60 * 24
    raise ValueError(f"Invalid time filter: [{since_time}]")
