
from .const import (
    START_COMMAND,

    EDIT_INTRO_COMMAND,
    EDIT_NAME_COMMAND,
    EDIT_CITY_COMMAND,
    EDIT_LINKS_COMMAND,
    EDIT_ABOUT_COMMAND,

    CANCEL_COMMAND,
    EMPTY_COMMAND,

    PARTICIPATE_COMMAND,
    PAUSE_WEEK_COMMAND,
    PAUSE_MONTH_COMMAND,

    SHOW_CONTACT_COMMAND,
    CONFIRM_CONTACT_COMMAND,
    FAIL_CONTACT_COMMAND,
    CONTACT_FEEDBACK_COMMAND
)


########
#   COMMAND
#######


COMMAND_DESCRIPTIONS = {
    START_COMMAND: 'инструкция, список команд',

    EDIT_INTRO_COMMAND: 'поменять анкету',
    EDIT_NAME_COMMAND: 'поменять имя',
    EDIT_CITY_COMMAND: 'поменять город',
    EDIT_LINKS_COMMAND: 'поменять ссылки',
    EDIT_ABOUT_COMMAND: 'поменять "о себе"',

    PARTICIPATE_COMMAND: 'участвовать во встречах',
    PAUSE_WEEK_COMMAND: 'пауза на неделю',
    PAUSE_MONTH_COMMAND: 'пауза на месяц',

    SHOW_CONTACT_COMMAND: 'контакт, анкета собеседника',
    CONFIRM_CONTACT_COMMAND: 'договорились о встрече',
    FAIL_CONTACT_COMMAND: 'не договорились/не отвечает',
    CONTACT_FEEDBACK_COMMAND: 'как прошла встреча',

    CANCEL_COMMAND: 'отменить',
    EMPTY_COMMAND: 'оставить пустым',
}


def command_description(command):
    return f'/{command} - {COMMAND_DESCRIPTIONS[command]}'


COMMANDS_TEXT = f'''{command_description(EDIT_INTRO_COMMAND)}
{command_description(EDIT_NAME_COMMAND)}
{command_description(EDIT_CITY_COMMAND)}
{command_description(EDIT_LINKS_COMMAND)}
{command_description(EDIT_ABOUT_COMMAND)}

{command_description(PARTICIPATE_COMMAND)}
{command_description(PAUSE_WEEK_COMMAND)}
{command_description(PAUSE_MONTH_COMMAND)}

{command_description(SHOW_CONTACT_COMMAND)}
{command_description(CONFIRM_CONTACT_COMMAND)}
{command_description(FAIL_CONTACT_COMMAND)}
{command_description(CONTACT_FEEDBACK_COMMAND)}

{command_description(START_COMMAND)}'''


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


######
#  START
######


def start_text(schedule):
    return f'''Бот организует random coffee для сообщества @natural_language_processing.

Инструкция:
1. Заполни короткую анкету /{EDIT_INTRO_COMMAND}.
2. Дай согласия на участие во встречах /{PARTICIPATE_COMMAND}. В понедельник {day_month(schedule.next_week_monday())} бот подберёт собеседника, пришлёт анкету и контакт.
3. Заходи в закрытый чат для первых участников https://t.me/+-A_Q6y-dODY3OTli. Там разработчик бота @alexkuk принимает баг репорты, рассказывает о новых фичах.

{COMMANDS_TEXT}'''


######
#  OTHER
######


OTHER_TEXT = f'''Бот ответчает только на команды.

{COMMANDS_TEXT}'''


######
#  INTRO
######


EMPTY_SYMBOL = '∅'


def intro_text(intro):
    return f'''Имя: {intro.name or EMPTY_SYMBOL}
Город: {intro.city or EMPTY_SYMBOL}
Ссылки: {intro.links or EMPTY_SYMBOL}
О себе: {intro.about or EMPTY_SYMBOL}'''


def edit_intro_text(intro):
    return f'''{intro_text(intro)}

{command_description(EDIT_NAME_COMMAND)}
{command_description(EDIT_CITY_COMMAND)}
{command_description(EDIT_LINKS_COMMAND)}
{command_description(EDIT_ABOUT_COMMAND)}

{command_description(CANCEL_COMMAND)}
{command_description(EMPTY_COMMAND)}'''


EDIT_NAME_TEXT = '''Напиши своё настоящее имя. Собеседник поймёт, как к тебе обращаться.'''

EDIT_CITY_TEXT = '''Напиши город, в котором живёшь. Собеседник поймет предлагать офлайн встречу или нет.'''

EDIT_LINKS_TEXT = '''Накидай ссылок про себя: блог, твиттер, фейсбук, канал, подкаст. Собеседник поймёт чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.

Примеры
- http://lab.alexkuk.ru, https://github.com/kuk, https://habr.com/ru/users/alexanderkuk/
- https://www.linkedin.com/in/alexkuk/, https://vk.com/alexkuk
- http://val.maly.hk'''

EDIT_ABOUT_TEXT = '''Напиши о себе. Собеседник поймёт чем ты занимаешься, о чём интересно спросить. Снимает неловкость в начале разговора.

Что писать?
- Где учился?
- Где успел поработать? Чем занимался, самое важное/удивительное?
- Сфера интересов в NLP? Проекты, статьи.
- Личное, чем занимаешься кроме работы? Спорт, игры. Где успел пожить?

Например
"Закончил ШАД, работал в Яндексе в поиске. Сделал библиотеку Nile, чтобы удобно ворочать логи на Мап Редьюсе https://habr.com/ru/company/yandex/blog/332688/.

Автор проекта Наташа https://github.com/natasha. Работаю в своей Лабе https://lab.alexkuk.ru, адаптирую Наташу под задачи клиентов.

Живу в Москве в Крылатском. У нас тут мекка велоспорта. Умею сидеть на колесе и сдавать смену. Вожу экскурсии. Могу рассказать про путь от академизма к супрематизму."'''

TOP_CITIES = [
    'Москва',
    'Санкт-Петербург',
    'Киев',
    'Минск',
    'Лондон',
    'Берлин',
]


#####
#  CONTACT
#####


def participate_text(schedule):
    return f'Пометил, что участвуешь во встречах. В понедельник {day_month(schedule.next_week_monday())} бот подберёт собеседника, пришлёт анкету и контакт.'


PAUSE_TEXT = 'Поставил встречи на паузу. Бот не будет присылать контакты собеседников и напоминания.'


def no_contact_text(schedule):
    return f'Бот не назначил тебе собеседника. Бот составляет пары по понедельникам, очередной раунд {day_month(schedule.next_week_monday())}.'


def user_mention(user):
    if user.username:
        return f'@{user.username}'
    elif user.intro.name:
        return user.intro.name
    return user.user_id


def user_url(user_id):
    return f'tg://user?id={user_id}'


def show_contact_text(user):
    return f'''Контакт собеседника в Телеграме: <a href="{user_url(user.user_id)}">{user_mention(user)}</a>.

{intro_text(user.intro)}

{command_description(CONFIRM_CONTACT_COMMAND)}
{command_description(FAIL_CONTACT_COMMAND)}
{command_description(CONTACT_FEEDBACK_COMMAND)}'''


CONFIRM_CONTACT_TEXT = f'Рад, что получилось договориться! Оставь фидбек после встречи /{CONTACT_FEEDBACK_COMMAND}.'


def fail_contact_text(schedule):
    return f'Жаль, что встреча не состоится. В понедельник {day_month(schedule.next_week_monday())} бот подберёт нового собеседника, пришлёт анкету и контакт.'


def contact_feedback_text(user):
    return f'''Собеседник: <a href="{user_url(user.user_id)}">{user_mention(user)}</a>

Оцени встречу:
1 - очень плохо
⋮
5 - очень хорошо

Или напиши фидбек своими словами.

{command_description(CANCEL_COMMAND)}
{command_description(EMPTY_COMMAND)}'''


CONTACT_FEEDBACK_OPTIONS = '12345'


def contact_feedback_state_text(user, contact):
    return f'Фидбек: "{contact.feedback or EMPTY_SYMBOL}"'
