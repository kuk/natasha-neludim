
import logging
import json

from .const import LOG_LEVEL


log = logging.getLogger(__name__)
log.setLevel(LOG_LEVEL)
log.addHandler(logging.StreamHandler())


def json_msg(**kwargs):
    return json.dumps(
        kwargs,
        ensure_ascii=False
    )
