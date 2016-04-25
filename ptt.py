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

    def set_board(self, board):
        prog = log.progress('Going to board "%s"...' % board)
        p = self.p
        p.sendline('s' + board + '\r')
        p.recvrepeat(1)
        p.send(' ')  # Skip banner or do nothing
        p.recvrepeat(0.1)
        prog.success('Done')

    def set_article(self, aid):
        prog = log.progress('Going to article "%s"...' % aid)
        p = self.p
        p.sendline(aid + '\r')
        p.recvrepeat(0.1)
        p.send('r')  # Enter article
        p.recvrepeat(0.1)
        prog.success('Done')

    def reload_article(self):
        p = self.p
        p.send('q')
        p.recvrepeat(0.1)
        p.send('r')
        p.recvrepeat(0.1)

    def get_last_page(self):
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
        self.set_board(board)
        self.set_article(aid)
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
        return re.sub('\033\\[[\\d;]*[mHK]', '', s)
