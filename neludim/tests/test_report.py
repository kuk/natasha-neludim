
from neludim.obj import (
    User,
    Contact
)
from neludim.const import (
    FAIL_STATE,
    CONFIRM_STATE,
    KRUTAN_TAG,
)
from neludim.report import (
    gen_report,
    report_text
)


def test_report():
    contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2, state=FAIL_STATE),
        Contact(week_index=0, user_id=2, partner_user_id=1, state=CONFIRM_STATE, feedback='4'),
        Contact(week_index=0, user_id=3, partner_user_id=None, state=FAIL_STATE, feedback='fail!'),
    ]
    users = [
        User(user_id=1, username='a', tags=[KRUTAN_TAG]),
        User(user_id=2, username='b'),
        User(user_id=3, name='C', paused=True),
    ]

    records = list(gen_report(users, contacts, week_index=0))
    assert report_text(records) == '''KR - krutan
P - pause
FT - first_time

C - confirm
F! - fail
NP - no_partner

KR ·  FT C  ·  @a
·  P  FT NP ·  C 
·  ·  FT C  4  @b'''
