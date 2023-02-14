
from dataclasses import (
    replace,
    fields,
    dataclass
)
from collections import defaultdict
from itertools import groupby

from .text import user_mention
from .const import (
    CONFIRM_STATE,
    FAIL_STATE,

    GREAT_SCORE,
    OK_SCORE,
    BAD_SCORE,
)


NO_PARTNER_STATE = 'no_partner'

STATES_ORDER = [
    CONFIRM_STATE,
    FAIL_STATE,
]

SHORT_STATES = {
    CONFIRM_STATE: 'C',
    FAIL_STATE: 'F!',
}
SHORT_SCORES = {
    GREAT_SCORE: 'G',
    OK_SCORE: 'OK',
    BAD_SCORE: 'B!',
}

NO_PARTNER_SYMBOL = 'NP'
CORNER_SYMBOLS = ['╭', '╰']


def propogate_contact_states(contacts):
    group_contacts = defaultdict(list)
    for contact in contacts:
        if contact.partner_user_id:
            user_id, partner_user_id = contact.user_id, contact.partner_user_id
            if user_id > partner_user_id:
                user_id, partner_user_id = partner_user_id, user_id
            group_contacts[user_id, partner_user_id].append(contact)
        else:
            yield replace(contact, state=NO_PARTNER_STATE)

    for group in group_contacts.values():
        states = {_.state for _ in group if _.state}
        has_feedback = any(_.feedback_score for _ in group)

        if has_feedback:
            state = CONFIRM_STATE
        elif states:
            if FAIL_STATE in states and CONFIRM_STATE in states:
                state = None
            elif CONFIRM_STATE in states:
                state = CONFIRM_STATE
            elif FAIL_STATE in states:
                state = FAIL_STATE
        else:
            state = None

        for contact in group:
            yield replace(contact, state=state)


def report_text(lines, html=False):
    text = '\n'.join(lines)

    if html:
        return '<pre>%s</pre>' % text

    return text


#######
#
#   MATCH REPORT
#
#######


@dataclass
class MatchReportRecord:
    user_id: int
    no_partner: bool
    state: str
    feedback_score: str


def gen_match_report(contacts, week_index):
    week_contacts = [
        _ for _ in contacts
        if _.week_index == week_index
    ]
    group_contacts = defaultdict(list)
    for contact in week_contacts:
        user_id, partner_user_id = contact.user_id, contact.partner_user_id
        if partner_user_id and user_id > partner_user_id:
            user_id, partner_user_id = partner_user_id, user_id
        group_contacts[user_id, partner_user_id].append(contact)

    def key(group):
        no_partner = len(group) == 1
        has_feedback = any(_.feedback_score for _ in group)
        states = {_.state for _ in group if _.state}

        if states:
            has_state = True
            state_order = min(STATES_ORDER.index(_) for _ in states)
        else:
            has_state = False
            state_order = None

        return (
            no_partner,
            not has_feedback,
            not has_state,
            state_order
        )

    for group in sorted(group_contacts.values(), key=key):
        for contact in group:
            yield MatchReportRecord(
                user_id=contact.user_id,
                no_partner=len(group) == 1,
                state=contact.state,
                feedback_score=contact.feedback_score
            )


def format_match_report(users, records):
    id_users = {_.user_id: _ for _ in users}

    for index, record in enumerate(records):
        user = id_users[record.user_id]
        mention = user_mention(user)

        state, feedback_score, corner = '   '

        if record.no_partner:
            state = NO_PARTNER_SYMBOL
        elif record.state:
            state = SHORT_STATES[record.state]

        if record.feedback_score:
            feedback_score = SHORT_SCORES[record.feedback_score]

        if state != NO_PARTNER_SYMBOL:
            corner = CORNER_SYMBOLS[index % 2]

        yield f'{corner} {state:<2} {feedback_score:>2} {mention}'


######
#
#   WEEKS REPORT
#
####


@dataclass
class WeeksReportRecord:
    week_index: int

    total: int = 0
    first_time: int = 0

    confirm_state: int = 0
    fail_state: int = 0
    none_state: int = 0

    great_feedback: int = 0
    ok_feedback: int = 0
    bad_feedack: int = 0
    none_feedback: int = 0


WEEKS_COLUMN_SYMBOLS = [
    'W',

    'T',
    'FT',

    'C',
    'F!',
    '∅',

    'G',
    'OK',
    'B!',
    '∅',
]


def gen_weeks_report(contacts):
    seen_user_ids = set()

    contacts = propogate_contact_states(contacts)
    contacts = sorted(contacts, key=lambda _: _.week_index)
    for week_index, week_contacts in groupby(contacts, key=lambda _: _.week_index):
        user_ids = set()
        user_id_states = {}
        user_id_feedback_scores = {}
        for contact in week_contacts:
            user_ids.add(contact.user_id)
            if contact.state:
                user_id_states[contact.user_id] = contact.state
            if contact.feedback_score:
                user_id_feedback_scores[contact.user_id] = contact.feedback_score

        record = WeeksReportRecord(week_index)
        for user_id in user_ids:
            record.total += 1
            if user_id not in seen_user_ids:
                record.first_time += 1

            state = user_id_states.get(user_id)
            if state is None:
                record.none_state += 1
            elif state == CONFIRM_STATE:
                record.confirm_state += 1
            elif state == FAIL_STATE:
                record.fail_state += 1

            feedback_score = user_id_feedback_scores.get(user_id)
            if state == CONFIRM_STATE:
                if feedback_score is None:
                    record.none_feedback += 1
                elif feedback_score == GREAT_SCORE:
                    record.great_feedback += 1
                elif feedback_score == OK_SCORE:
                    record.ok_feedack += 1
                elif feedback_score == BAD_SCORE:
                    record.bad_feedack += 1

        seen_user_ids.update(user_ids)
        yield record


def format_weeks_report(records):
    for index, record in enumerate(records):
        if index % 5 == 0:
            yield ' '.join(_.rjust(2) for _ in WEEKS_COLUMN_SYMBOLS)

        values = [
            getattr(record, _.name)
            for _ in fields(record)
        ]
        yield ' '.join(str(_).rjust(2) for _ in values)
