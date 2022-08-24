
import sys
import argparse

from .context import Context
from .bot.webhook import start_webhook as bot_webhook
from .trigger import start_webhook as trigger_webhook


def build_parser():
    parser = argparse.ArgumentParser(prog='neludim')
    parser.set_defaults(function=None)
    subs = parser.add_subparsers()

    sub = subs.add_parser('bot-webhook')
    sub.set_defaults(function=bot_webhook)

    sub = subs.add_parser('trigger-webhook')
    sub.set_defaults(function=trigger_webhook)

    return parser


def run(parser, argv):
    args = parser.parse_args(argv[1:])
    if not args.function:
        parser.print_help()
        parser.exit()

    try:
        context = Context()
        args.function(context)
    except (KeyboardInterrupt, BrokenPipeError):
        pass


def main():
    parser = build_parser()
    run(parser, sys.argv)
