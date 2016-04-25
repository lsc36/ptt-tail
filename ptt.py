# -*- coding: utf8 -*-
import re
import time

from pwn import remote
from pwn import log


class Ptt(object):

    def __init__(self, user, passwd):
        prog = log.progress('Logging in...')
        p = remote('ptt.cc', 23)
        p.recvrepeat(0.1)  # Login screen
        p.sendline(user + ',\r')
        p.recvrepeat(0.1)  # Enter password
        p.sendline(passwd + '\r')
        if p.recvrepeat(1).find('您想刪除其他重複登入的連線嗎') != -1:
            p.sendline('n\r')
        p.recvuntil('請按任意鍵繼續')
        p.sendline('\r')
        p.recvrepeat(0.1)
        prog.success('Done')
        self.p = p
        self._board = None
        self._article = None

    @property
    def board(self):
        return self._board

    @board.setter
    def board(self, board):
        prog = log.progress('Going to board "%s"...' % board)
        p = self.p
        p.sendline('s' + board + '\r')
        p.recvrepeat(1)
        p.send(' ')  # Skip banner or do nothing
        p.recvrepeat(0.1)
        prog.success('Done')
        self._board = board
        self._article = None

    @property
    def article(self):
        return self._article

    @article.setter
    def article(self, aid):
        if self._board is None:
            raise ValueError('Board not set')
        prog = log.progress('Going to article "%s"...' % aid)
        p = self.p
        p.sendline(aid + '\r')
        p.recvrepeat(0.1)
        p.send('r')  # Enter article
        p.recvrepeat(0.1)
        prog.success('Done')
        self._article = aid

    def reload_article(self):
        if self._article is None:
            raise ValueError('Article not set')
        p = self.p
        p.send('q')
        p.recvrepeat(0.1)
        p.send('r')
        p.recvrepeat(0.1)

    def get_last_page(self):
        if self._article is None:
            raise ValueError('Article not set')
        p = self.p
        p.send('$')  # End
        p.recvrepeat(0.1)

        while True:
            p.send('\x0c')  # Ctrl-L re-render screen
            lines = p.recvrepeat(0.1).split('\r\n')[:-1]
            if lines:
                break
            log.warn('Re-render failed, retrying')

        lines = map(Ptt.noctrl, lines)
        lines = map(lambda l: l.strip(), lines)
        return lines

    def tail(self, board, aid, poll_interval=5):
        self.board = board
        self.article = aid
        last = self.get_last_page()
        for l in last:
            yield Ptt.push_format(l) + (False,)  # Not follow
        while True:
            try:
                time.sleep(poll_interval)
                self.reload_article()
                cur = self.get_last_page()
                # Find new pushes
                pos = len(cur)
                while pos > 0:
                    if last[-1] == cur[pos - 1]:
                        break
                    pos -= 1
                if pos == 0:
                    log.warn('New pushes more than 1 page, some may be lost')
                for l in cur[pos:]:
                    yield Ptt.push_format(l) + (True,)  # Follow
                last = cur
            except KeyboardInterrupt:
                break

    @staticmethod
    def push_format(s_orig):
        s = Ptt.noctrl(s_orig)
        m = re.match(r'^([^ ]+) ([\w]+) *: (.*) (\d\d/\d\d \d\d:\d\d)$', s.strip())
        if m is None:
            log.warn('Error parsing push: ' + repr(s_orig))
            return None, None, None, s
        push_type = m.group(1)
        # Replace Unicode arrow with ASCII chars (weird width on terminal)
        if push_type == '\x08\x08→':
            push_type = '->'
        return m.group(4), push_type, m.group(2), m.group(3)

    @staticmethod
    def noctrl(s):
        # Remove terminal control chars
        return re.sub('\033\\[[\\d;]*[mHJK]', '', s)
