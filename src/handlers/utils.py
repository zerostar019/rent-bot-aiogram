from datetime import date


def is_past(day, month, year):
    today = date.today()
    return year < today.year or (year == today.year and month < today.month) or (year == today.year and month == today.month and day < today.day)


print(is_past(day=1, month=1, year=2024))