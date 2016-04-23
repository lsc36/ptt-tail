#!/usr/bin/env python
import argparse

import config
from ptt import Ptt


def main():
    parser = argparse.ArgumentParser(description='Tail and follow the given PTT article.')
    parser.add_argument('board', help='name of the board')
    parser.add_argument('aid', help='AID of the article (remember to escape "#")')
    args = parser.parse_args()
    ptt = Ptt(config.user, config.passwd)
    for time, push_type, user, msg in ptt.tail(args.board, args.aid):
        if time is None:
            # Error parsing, print raw
            print msg
        else:
            print '%s %s %s: %s' % (time, push_type, user, msg)
        for hook in (
                config.hooks.get('*', {}).get('*', []) +
                config.hooks.get('*', {}).get(args.aid, []) +
                config.hooks.get(args.board, {}).get('*', []) +
                config.hooks.get(args.board, {}).get(args.aid, [])
                ):
            hook(time, push_type, user, msg)


if __name__ == '__main__':
    main()
