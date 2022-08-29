
import random

from neludim.obj import Match


def gen_matches(users, skip_matches=(), manual_matches=(), seed=0):
    random.seed(seed)

    user_ids = {_.user_id for _ in users}
    skip_match_keys = {_.key for _ in skip_matches}

    manual_matches = sorted(
        manual_matches,
        key=lambda _: (_.weight or 0, random.random()),
        reverse=True
    )

    matched_user_ids = set()
    for match in manual_matches:
        user_id, partner_user_id = match.key

        if user_id in matched_user_ids or partner_user_id in matched_user_ids:
            continue

        if user_id not in user_ids or partner_user_id not in user_ids:
            continue

        if (
                (user_id, partner_user_id) in skip_match_keys
                or (partner_user_id, user_id) in skip_match_keys
        ):
            continue

        matched_user_ids.add(user_id)
        matched_user_ids.add(partner_user_id)
        yield Match(user_id, partner_user_id)

    for user in users:
        if user.user_id in matched_user_ids:
            continue

        partner_users = []
        for partner_user in users:
            if partner_user == user:
                continue

            if partner_user.user_id in matched_user_ids:
                continue

            if (
                    (user.user_id, partner_user.user_id) in skip_match_keys
                    or (partner_user.user_id, user.user_id) in skip_match_keys
            ):
                continue

            partner_users.append(partner_user)

        if not partner_users:
            yield Match(user.user_id, partner_user_id=None)
            continue

        partner_user = random.choice(partner_users)
        matched_user_ids.add(user.user_id)
        matched_user_ids.add(partner_user.user_id)
        yield Match(user.user_id, partner_user.user_id)
