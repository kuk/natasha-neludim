
from neludim.obj import (
    User,
    Match,
    Contact
)
from neludim.match import gen_matches


def test_even():
    users = [User(user_id=_) for _ in range(4)]
    matches = list(gen_matches(users))
    assert matches == [
        Match(user_id=0, partner_user_id=1),
        Match(user_id=2, partner_user_id=3)
    ]


def test_odd():
    users = [User(user_id=_) for _ in range(3)]
    matches = list(gen_matches(users))
    assert matches == [
        Match(user_id=0, partner_user_id=1),
        Match(user_id=2, partner_user_id=None)
    ]


def test_manual():
    users = [User(user_id=_) for _ in range(5)]
    manual_matches = [
        Match(0, 2),
        Match(1, 2),
        Match(1, 4)
    ]
    matches = list(gen_matches(users, manual_matches=manual_matches))
    assert matches == [
        Match(user_id=1, partner_user_id=4),
        Match(user_id=0, partner_user_id=2),
        Match(user_id=3, partner_user_id=None),
    ]


def test_skip():
    users = [User(user_id=_) for _ in range(5)]
    contacts = [
        Contact(1, 0, 1),
        Contact(1, 0, 2),
        Contact(1, 1, 2),
        Contact(1, 1, 4)
    ]
    matches = list(gen_matches(users, contacts=contacts, current_week_index=2))
    assert matches == [
        Match(user_id=0, partner_user_id=3),
        Match(user_id=2, partner_user_id=4),
        Match(user_id=1, partner_user_id=None),
    ]
