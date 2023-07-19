
from neludim.obj import (
    User,
    Contact
)
from neludim.report import (
    gen_match_report,
    format_match_report,
    gen_weeks_report,
    format_weeks_report,
    report_text
)
from neludim.const import (
    FAIL_STATE,
    CONFIRM_STATE,
    BAD_SCORE,
)


def test_match_report():
    contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2, state=FAIL_STATE),
        Contact(week_index=0, user_id=2, partner_user_id=1, state=CONFIRM_STATE, feedback_score=BAD_SCORE),
        Contact(week_index=0, user_id=3, partner_user_id=None),
    ]
    users = [
        User(user_id=1, username='a'),
        User(user_id=2, username='b'),
        User(user_id=3, name='C'),
    ]
    id_users = {_.user_id: _ for _ in users}

    records = gen_match_report(contacts, prev_contacts=(), manual_matches=())
    lines = format_match_report(records, id_users)
    assert report_text(lines) == '''
  ╭ F!    @a
  ╰ C  B! @b
    NP    C
'''.strip('\n')


def test_weeks_report():
    contacts = [
        Contact(week_index=0, user_id=1, partner_user_id=2, state=FAIL_STATE),
        Contact(week_index=0, user_id=2, partner_user_id=1, state=CONFIRM_STATE, feedback_score=BAD_SCORE),
        Contact(week_index=1, user_id=1, partner_user_id=None),
    ]

    records = gen_weeks_report(contacts)
    lines = format_weeks_report(records)
    assert report_text(lines) == '''
 T FT NP   C F!  ∅   +  -  ∅
 2  2  0   0  0  2   0  0  0
 1  0  1   0  0  0   0  0  0
'''.strip('\n')
