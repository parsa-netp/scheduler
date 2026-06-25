from datetime import datetime, timedelta


def parse_dt_safe(dt_str: str) -> datetime:
    if " 24:00:00" in dt_str:
        dt_str = dt_str.replace(" 24:00:00", " 00:00:00")
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
