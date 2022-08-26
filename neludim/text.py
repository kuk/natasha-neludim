
#######
#  DATETIME
#####


MONTHS = {
    1: 'января',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря',
}


def day_month(datetime):
    return f'{datetime.day} {MONTHS[datetime.month]}'


def day_day_month(start, stop):
    if start.month == stop.month:
        return f'{start.day}-{stop.day} {MONTHS[start.month]}'
    else:
        return f'{day_month(start)} - {day_month(stop)}'


########
#  USER
######


def user_mention(user):
    if user.username:
        return f'@{user.username}'
    elif user.intro.name:
        return user.intro.name
    return user.user_id


def user_url(user_id):
    return f'tg://user?id={user_id}'


EMPTY_SYMBOL = '∅'


def intro_text(intro):
    return f'''Имя: {intro.name or EMPTY_SYMBOL}
Город: {intro.city or EMPTY_SYMBOL}
Ссылки: {intro.links or EMPTY_SYMBOL}
О себе: {intro.about or EMPTY_SYMBOL}'''
