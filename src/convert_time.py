from datetime import datetime, timedelta

async def convert_time(date: str, hour: str):
    new_hour = hour
    if len(hour) == 1:
        new_hour = f'0{hour}:00'
    
    date = date + ' ' + new_hour

    format_string = "%Y-%m-%d %H:%M"

    new_date = datetime.strptime(date, format_string) + timedelta(hours=1)

    return new_date