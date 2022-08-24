
import sys
import argparse

from .context import Context


def bot_webhook(context, args):
    from .bot.bot import setup_bot
    from .bot.webhook import start_webhook

    setup_bot(context)
    start_webhook(context)


def trigger_webhook(context, args):
    from .trigger import start_webhook

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
        context = Context()
        args.function(context, args)
    except (KeyboardInterrupt, BrokenPipeError):
        pass


def main():
    parser = build_parser()
    run(parser, sys.argv)
