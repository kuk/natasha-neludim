
import random

from .obj import Match
from .const import GREAT_SCORE


def is_repeat_contact(contact, current_week_index):
    return (
    )


def gen_matches(users, manual_matches=(), contacts=(), current_week_index=0, seed=0):
    # <100 users per week, ok to have O(N^2) algo
    random.seed(seed)

    contacts_index = {}
    for contact in contacts:
        if contact.partner_user_id:
            contacts_index[contact.user_id, contact.partner_user_id] = contact
            contacts_index[contact.partner_user_id, contact.user_id] = contact

    manual_matches_index = set()
    for match in manual_matches:
        manual_matches_index.add((match.user_id, match.partner_user_id))
        manual_matches_index.add((match.partner_user_id, match.user_id))

    def score_match(user, partner_user):
        contact = contacts_index.get((user.user_id, partner_user.user_id))

        is_repeat_contact = False
        if (
                contact
                and contact.feedback_score == GREAT_SCORE
                and current_week_index - contact.week_index > 12
        ):
            is_repeat_contact = True

        if contact and not is_repeat_contact:
            return

        is_manual_match = (
            (user.user_id, partner_user.user_id) in manual_matches_index
            and not contact
        )

        has_about = user.links is not None or user.about is not None
        partner_has_about = partner_user.links is not None or partner_user.about is not None
        match_about = (
            has_about and partner_has_about
            or not has_about and not partner_has_about
        )

        same_city = False
        if user.city and partner_user.city:
            same_city = user.city == partner_user.city

        return (
            is_manual_match,
            match_about,
            same_city,
            not is_repeat_contact,

            # shuffle same
            random.random()
        )

    match_scores = {}
    for user in users:
        for partner_user in users:
            if user.user_id >= partner_user.user_id:
                continue

            score = score_match(user, partner_user)
            if score:
                match_scores[user.user_id, partner_user.user_id] = score

    matched_user_ids = set()
    for user_id, partner_user_id in sorted(match_scores, key=match_scores.get, reverse=True):
        if (
                user_id in matched_user_ids
                or partner_user_id in matched_user_ids
        ):
            continue

        matched_user_ids.update((user_id, partner_user_id))
        yield Match(user_id, partner_user_id)

    for user in users:
        if user.user_id not in matched_user_ids:
            yield Match(user.user_id, partner_user_id=None)
