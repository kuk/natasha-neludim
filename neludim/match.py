
import random
from collections import (
    defaultdict,
    Counter
)

from neludim.obj import Match


def gen_matches(users, skip_matches=(), manual_matches=(), seed=0):
    random.seed(seed)

    user_ids = {_.user_id for _ in users}

    skip_matches_index = defaultdict(set)
    for match in skip_matches:
        skip_matches_index[match.user_id].add(match.partner_user_id)
        skip_matches_index[match.partner_user_id].add(match.user_id)

    manual_matches_index = defaultdict(set)
    for match in manual_matches:
        if (
                match.user_id in user_ids and match.partner_user_id in user_ids
                and match.partner_user_id not in skip_matches_index[match.user_id]
        ):
            manual_matches_index[match.user_id].add(match.partner_user_id)
            manual_matches_index[match.partner_user_id].add(match.user_id)

    city_weights = Counter(
        _.city for _ in users
        if _.city
    )

    def key(user):
        has_manual_match = user.user_id in manual_matches_index
        tags_count = len(user.tags)

        has_about = (
            user.links is not None
            or user.about is not None
        )

        city_weight = 0
        if user.city:
            city_weight = city_weights[user.city]

        return (
            has_manual_match,
            tags_count,
            has_about,
            city_weight,

            # shuffle inside groups
            random.random()
        )

    users = sorted(users, key=key, reverse=True)

    matched_user_ids = set()
    for user in users:
        if user.user_id in matched_user_ids:
            continue

        # <100 users per week, ok N(O^2) algo
        partner_users = [
            _ for _ in users
            if _.user_id != user.user_id
            if _.user_id not in matched_user_ids
            if _.user_id not in skip_matches_index[user.user_id]
        ]

        partner_user_id = None
        if partner_users:

            def key(partner_user, user=user):
                is_manual_match = partner_user.user_id in manual_matches_index[user.user_id]
                tags_intersection = len(set(user.tags) & set(partner_user.tags))

                same_city = False
                if user.city and partner_user.city:
                    same_city = user.city == partner_user.city

                return (
                    is_manual_match,
                    tags_intersection,
                    same_city
                )

            # key is similarity, bigger better
            partner_users = sorted(partner_users, key=key, reverse=True)
            partner_user_id = partner_users[0].user_id

        matched_user_ids.add(user.user_id)
        matched_user_ids.add(partner_user_id)
        yield Match(user.user_id, partner_user_id)
