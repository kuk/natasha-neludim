
import logging
from os import getenv


#######
#  SECRETS
######

# Ask @alexkuk for .env

BOT_TOKEN = getenv('BOT_TOKEN')

AWS_KEY_ID = getenv('AWS_KEY_ID')
AWS_KEY = getenv('AWS_KEY')

DYNAMO_ENDPOINT = getenv('DYNAMO_ENDPOINT')

ADMIN_USER_ID = int(getenv('ADMIN_USER_ID'))

#####
#  LOG
#####

LOG_LEVEL = getenv('LOG_LEVEL', logging.INFO)

#####
#  STATE
######

EDIT_NAME_STATE = 'edit_name'
EDIT_CITY_STATE = 'edit_city'
EDIT_LINKS_STATE = 'edit_links'
EDIT_ABOUT_STATE = 'edit_about'

CONTACT_FEEDBACK_STATE = 'contact_feedback'

CONFIRM_STATE = 'confirm'
FAIL_STATE = 'fail'

######
#  PERIOD
#####

WEEK = 'week'
MONTH = 'month'

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
#  TAGS
#######

KRUTAN = 'krutan'
RESEARCH = 'research'

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

EDIT_PROFILE_COMMAND = 'edit_profile'
EDIT_NAME_COMMAND = 'edit_name'
EDIT_CITY_COMMAND = 'edit_city'
EDIT_LINKS_COMMAND = 'edit_links'
EDIT_ABOUT_COMMAND = 'edit_about'

CANCEL_COMMAND = 'cancel'
EMPTY_COMMAND = 'empty'

PARTICIPATE_COMMAND = 'participate'
PAUSE_WEEK_COMMAND = 'pause_week'
PAUSE_MONTH_COMMAND = 'pause_month'

SHOW_CONTACT_COMMAND = 'show_contact'
CONFIRM_CONTACT_COMMAND = 'confirm_contact'
FAIL_CONTACT_COMMAND = 'fail_contact'
CONTACT_FEEDBACK_COMMAND = 'contact_feedback'

######
#  PORT
#####

PORT = getenv('PORT', 8080)
