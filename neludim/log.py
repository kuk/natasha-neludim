
import logging
import json


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


def json_msg(**kwargs):
    return json.dumps(
        kwargs,
        ensure_ascii=False
    )
