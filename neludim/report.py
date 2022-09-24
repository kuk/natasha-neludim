
from dataclasses import dataclass
from collections import defaultdict

from .const import (
    CONFIRM_STATE,
    FAIL_STATE,
    KRUTAN_TAG,
)
from .text import user_mention


NO_PARTNER_STATE = 'no_partner'


@dataclass
class ReportRecord:
    mention: str
    is_krutan: bool
    paused: bool
    first_time: bool
    state: str
    feedback: str


def propogate_contact_states(contacts):
    # If has feedback -> confirmed
    # If any confirmed -> both confirmed
    # If any failed -> both failed
    # Treat confirmed, failed as none, none

    group_contacts = defaultdict(list)
    for contact in contacts:
        if contact.partner_user_id:
            user_id, partner_user_id = contact.user_id, contact.partner_user_id
            if user_id > partner_user_id:
                user_id, partner_user_id = partner_user_id, user_id
            group_contacts[user_id, partner_user_id].append(contact)

    for group in group_contacts.values():
        states = {_.state for _ in group if _.state}
        feedbacks = {_.feedback for _ in group if _.feedback}

        state = None
        if feedbacks:
            state = CONFIRM_STATE
        else:
            if CONFIRM_STATE in states and FAIL_STATE in states:
                state = None
            elif CONFIRM_STATE in states:
                state = CONFIRM_STATE
            elif FAIL_STATE in states:
                state = FAIL_STATE

        for contact in group:
            contact.state = state


def gen_report(users, contacts, week_index):
    previous_weeks_user_ids = set()
    week_user_ids = set()
    next_week_user_ids = set()
    week_contacts = []
    for contact in contacts:
        if contact.week_index < week_index:
            previous_weeks_user_ids.update((contact.user_id, contact.partner_user_id))
        elif contact.week_index == week_index:
            week_user_ids.update((contact.user_id, contact.partner_user_id))
            week_contacts.append(contact)
        elif contact.week_index == week_index + 1:
            next_week_user_ids.update((contact.user_id, contact.partner_user_id))

    propogate_contact_states(week_contacts)

    user_id_contacts = defaultdict(list)
    for contact in week_contacts:
        user_id_contacts[contact.user_id].append(contact)

    id_users = {_.user_id: _ for _ in users}

    for user_id, contacts in user_id_contacts.items():
        user = id_users[user_id]

        if next_week_user_ids:
            paused = user_id not in next_week_user_ids
        else:
            # Current week
            paused = bool(user.paused)

        first_time = user_id not in previous_weeks_user_ids

        partner_contacts = [_ for _ in contacts if _.partner_user_id]

        state = None
        if not partner_contacts:
            state = NO_PARTNER_STATE
        else:
            states = {_.state for _ in partner_contacts}
            if CONFIRM_STATE in states:
                state = CONFIRM_STATE
            elif FAIL_STATE in states:
                state = FAIL_STATE

        for contact in partner_contacts:
            if contact.state == CONFIRM_STATE and contact.feedback:
                feedback = contact.feedback
                break
        else:
            feedback = None

        mention = user_mention(user)
        is_krutan = KRUTAN_TAG in (user.tags or [])

        yield ReportRecord(
            mention=mention,
            is_krutan=is_krutan,
            paused=paused,
            first_time=first_time,
            state=state,
            feedback=feedback
        )


EMPTY_SYMBOL = '·'
SHORT_STATES = {
    CONFIRM_STATE: 'C',
    FAIL_STATE: 'F!',
    NO_PARTNER_STATE: 'NP'
}

ABBRS = '''KR - krutan
P - pause
FT - first_time

C - confirm
F! - fail
NP - no_partner
'''


def format_report_record(record):
    yield 'KR' if record.is_krutan else EMPTY_SYMBOL
    yield 'P' if record.paused else EMPTY_SYMBOL
    yield 'FT' if record.first_time else EMPTY_SYMBOL

    if record.state:
        yield SHORT_STATES[record.state]
    else:
        yield EMPTY_SYMBOL

    if record.feedback:
        if record.feedback in '12345':
            yield record.feedback
        else:
            yield '…'
    else:
        yield EMPTY_SYMBOL

    yield record.mention


def format_report(records):
    def key(record):
        return (
            record.is_krutan,
            record.paused,
            record.first_time,
            record.state or EMPTY_SYMBOL,
        )

    yield ABBRS

    records = sorted(records, key=key, reverse=True)  # False first
    for record in records:
        parts = format_report_record(record)
        yield ' '.join(_.ljust(2) for _ in parts)


def report_text(records):
    lines = format_report(records)
    return '\n'.join(lines)
