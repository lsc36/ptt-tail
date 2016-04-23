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
    ptt.tail(args.board, args.aid)


if __name__ == '__main__':
    main()
