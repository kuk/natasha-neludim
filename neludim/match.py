
# Current week users form a graph. At week=0 graph as fully
# connected. Edges for users who met are removed. Edges have weight,
# for example edge between users are from same city > edge between
# diff cities, etc. Algo greedy connect users, first users with max
# weight edge. Assume <100 users per week, OK to have O(N^2)
# algo. Order of edges with same weight in random. Random order leads
# to non optimal matches, simples examples with 4 participants:

# A-B-C-D  (A-D, A-C, A-D, ... already met)

# Image algo selects B-C first, then A and D are left with no pair. It
# would be better to select A-B first then C-D, end up with no no
# pairs.

# To alleviate this problem algo repeat procedure 10 times, returns
# matches with miniman number of no pairs.


import random
from dataclasses import dataclass
from collections import defaultdict

from .obj import Match
from .const import (
    CONFIRM_STATE,
    FAIL_STATE,

    BAD_SCORE,
    OK_SCORE,
    GREAT_SCORE
)


@dataclass
class SampleMatch:
    user_id: int
    partner_user_id: int
    is_new: bool


def gen_matches_sample(users, stats, current_week_index, seed=0):
    key_week_indexes, key_states, key_feedback_scores, manual_match_keys = stats
    random.seed(seed)

    def score_match(user, partner_user):
        key = user.user_id, partner_user.user_id

        do_repeat = False
        week_index = key_week_indexes.get(key)
        if week_index is not None:
            feedback_score = key_feedback_scores[key]
            if (
                    feedback_score == GREAT_SCORE
                    and current_week_index - week_index > 8
            ):
                do_repeat = True

            state = key_states[key]
            if (
                    state != CONFIRM_STATE
                    and current_week_index - week_index > 4
            ):
                do_repeat = True

            if not do_repeat:
                return

        is_manual_match = key in manual_match_keys

        has_about = user.links is not None or user.about is not None
        partner_has_about = partner_user.links is not None or partner_user.about is not None
        match_about = (
            has_about and partner_has_about
            or not has_about and not partner_has_about
        )

        same_city = False
        if user.city and partner_user.city:
            same_city = user.city == partner_user.city

        is_new = not do_repeat
        return (
            is_new,
            is_manual_match,
            same_city,
            match_about,

            # shuffle same
            random.random()
        )

    score_keys = []
    for user in users:
        for partner_user in users:
            if user.user_id >= partner_user.user_id:
                continue

            score = score_match(user, partner_user)
            if score:
                key = user.user_id, partner_user.user_id
                score_keys.append((score, key))

    matched_user_ids = set()
    for score, (user_id, partner_user_id) in sorted(score_keys, reverse=True):
        if (
                user_id in matched_user_ids
                or partner_user_id in matched_user_ids
        ):
            continue

        matched_user_ids.add(user_id)
        matched_user_ids.add(partner_user_id)

        is_new, *_ = score
        yield SampleMatch(user_id, partner_user_id, is_new)


def sort2(a, b):
    if a > b:
        return b, a
    return a, b


def gen_matches(users, manual_matches, contacts, current_week_index=0, rounds=10):
    key_contacts = defaultdict(list)
    for contact in sorted(contacts, key=lambda _: _.week_index):
        if contact.partner_user_id:
            key = sort2(contact.user_id, contact.partner_user_id)
            key_contacts[key].append(contact)

    key_week_indexes = {}
    key_states = {}
    key_feedback_scores = {}
    for key, group in key_contacts.items():
        key_week_indexes[key] = max(_.week_index for _ in group)

        states = {_.state for _ in group}
        for state in [CONFIRM_STATE, FAIL_STATE, None]:
            if state in states:
                key_states[key] = state
                break

        feedback_scores = {_.feedback_score for _ in group}
        for feedback_score in [BAD_SCORE, OK_SCORE, GREAT_SCORE, None]:
            if feedback_score in feedback_scores:
                key_feedback_scores[key] = feedback_score
                break

    manual_match_keys = set()
    for match in manual_matches:
        key = sort2(match.user_id, match.partner_user_id)
        manual_match_keys.add(key)

    stats = (key_week_indexes, key_states, key_feedback_scores, manual_match_keys)

    def score_sample(matches):
        matched_count = len(matches)
        is_new_count = sum(_.is_new for _ in matches)
        return (
            matched_count,
            is_new_count,
            random.random()
        )

    score_samples = []
    for seed in range(rounds):
        sample = list(gen_matches_sample(
            users, stats,
            current_week_index=current_week_index,
            seed=seed
        ))
        score = score_sample(sample)
        score_samples.append((score, sample))

    _, sample = max(score_samples)

    matched_user_ids = set()
    for match in sample:
        user_id, partner_user_id = match.user_id, match.partner_user_id
        matched_user_ids.add(user_id)
        matched_user_ids.add(partner_user_id)
        yield Match(user_id, partner_user_id)

    for user in users:
        if user.user_id not in matched_user_ids:
            yield Match(user.user_id, partner_user_id=None)
