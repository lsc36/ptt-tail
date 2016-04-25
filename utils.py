import re


"""Decorator for hooks to activate if message matches any of given regex."""
def regex_match(*rlist):
    def _deco(func):
        def _wrap(time, ptype, user, msg):
            if any(re.search(r, msg) is not None for r in rlist):
                return func(time, ptype, user, msg)
        return _wrap
    return _deco
