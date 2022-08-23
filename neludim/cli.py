
import sys
import argparse

from .context import Context


def bot_webhook(args):
    from .bot.middlewares import setup_middlewares
    from .bot.filters import setup_filters
    from .bot.handlers import setup_handlers
    from .bot.webhook import start_webhook

    context = Context()
    setup_middlewares(context)
    setup_filters(context)
    setup_handlers(context)
    start_webhook(context)


def trigger_webhook(args):
    from .trigger import start_webhook

    context = Context()
    start_webhook(context)


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
        args.function(args)
    except (KeyboardInterrupt, BrokenPipeError):
        pass


def main():
    parser = build_parser()
    run(parser, sys.argv)
