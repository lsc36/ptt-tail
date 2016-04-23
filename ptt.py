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

    def get_last_page(self, aid):
        p = self.p
        p.sendline(aid + '\r')
        p.recvrepeat(0.1)
        p.sendline('\r')  # Enter article
        p.recvrepeat(0.1)
        p.send('$')  # End
        p.recvrepeat(0.1)

        # Receive pushes line by line to prevent weird control chars
        p.send('\033[5~')  # PgUp
        p.recvrepeat(0.1)

        lines = []
        while True:
            p.send('\033[B')  # Down
            s = p.recvrepeat(0.1)
            l = s.split('\r\n')
            for ll in l[:-1]:
                lines.append(ll)
            if l[-1].find('100%') != -1:
                p.send('q')
                break
        return lines

    def tail(self, board, aid, poll_interval=5):
        self.set_board(board)
        last = self.get_last_page(aid)
        for l in last:
            print Ptt.push_format(l)
        while True:
            try:
                time.sleep(poll_interval)
                cur = self.get_last_page(aid)
                # Find new pushes
                pos = len(cur)
                while pos > 0:
                    if last[-1] == cur[pos - 1]:
                        break
                    pos -= 1
                for l in cur[pos:]:
                    print Ptt.push_format(l)
                last = cur
            except KeyboardInterrupt:
                break

    @staticmethod
    def push_format(s_orig):
        s = Ptt.noctrl(s_orig)
        m = re.match(r'^([^ ]+) ([\w]+): (.*) (\d\d/\d\d \d\d:\d\d)$', s.strip())
        if m is None:
            log.warn('Error parsing push: ' + repr(s_orig))
            return s
        push_type = m.group(1)
        # Replace Unicode arrow with ASCII chars (weird width on terminal)
        if push_type == '\x08\x08→':
            push_type = '->'
        return '%s %s %s: %s' % (m.group(4), push_type, m.group(2), m.group(3))

    @staticmethod
    def noctrl(s):
        # Remove terminal control chars
        return re.sub('\033\\[[\\d;]*[mHK]', '', s)
