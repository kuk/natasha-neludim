
from os import (
    getenv,
    environ
)

from .env import (
    find_dotenv,
    load_dotenv
)


#######
#  SECRETS
######

# Ask @alexkuk for .env
path = find_dotenv()
if path:
    environ.update(load_dotenv(path))

BOT_TOKEN = getenv('BOT_TOKEN')

AWS_KEY_ID = getenv('AWS_KEY_ID')
AWS_KEY = getenv('AWS_KEY')

DYNAMO_ENDPOINT = getenv('DYNAMO_ENDPOINT')

ADMIN_USER_ID = int(getenv('ADMIN_USER_ID'))

#######
#  CONTACT STATE
######

CONFIRM_STATE = 'confirm'
FAIL_STATE = 'fail'

#####
#  SCHEDULE
#######

MONDAY = 'monday'
TUESDAY = 'tuesday'
WEDNESDAY = 'wednesday'
THURSDAY = 'thursday'
FRIDAY = 'friday'
SATURDAY = 'saturday'
SUNDAY = 'sunday'

WEEKDAYS = [
    MONDAY,
    TUESDAY,
    WEDNESDAY,
    THURSDAY,
    FRIDAY,
    SATURDAY,
    SUNDAY
]

#####
#  DYNAMO
####

BOOL = 'BOOL'
N = 'N'
S = 'S'
M = 'M'
SS = 'SS'

######
#  DB
#####

CHATS_TABLE = 'chats'
CHATS_KEY = 'id'

USERS_TABLE = 'users'
USERS_KEY = 'user_id'

CONTACTS_TABLE = 'contacts'
CONTACTS_KEY = 'key'

MANUAL_MATCHES_TABLE = 'manual_matches'
MANUAL_MATCHES_KEY = 'key'

#####
#  COMMAND
#######

START_COMMAND = 'start'
HELP_COMMAND = 'help'

######
#  DATA
######

EDIT_PROFILE_PREFIX = 'edit_profile'
PARTICIPATE_PREFIX = 'participate'
FEEDBACK_PREFIX = 'feedback'
REVIEW_PROFILE_PREFIX = 'review_profile'

CANCEL_EDIT_DATA = 'cancel_edit'
CANCEL_FEEDBACK_DATA = 'cancel_feedback'

####
#  PROFILE FIELD
####

NAME_FIELD = 'name'
CITY_FIELD = 'city'
LINKS_FIELD = 'links'
ABOUT_FIELD = 'about'

#####
#  STATE
#####

CONFIRM_STATE = 'confirm'
FAIL_STATE = 'fail'

####
#  ACTION
#####

CONFIRM_ACTION = 'confirm'
MATCH_ACTION = 'match'

#####
#  SCORE
###

GREAT_SCORE = 'great'
OK_SCORE = 'ok'
BAD_SCORE = 'bad'

######
#  PORT
#####

PORT = getenv('PORT', 8080)
