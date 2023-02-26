
#######
#
#  DATETIME
#
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


########
#
#  USER
#
######


def user_mention(user):
    if user.username:
        return f'@{user.username}'
    elif user.name:
        return user.name
    return user.user_id


EMPTY_SYMBOL = '∅'


def profile_text(user):
    return f'''Имя: {user.name or EMPTY_SYMBOL}
Город: {user.city or EMPTY_SYMBOL}
Ссылки: {user.links or EMPTY_SYMBOL}
О себе: {user.about or EMPTY_SYMBOL}'''
