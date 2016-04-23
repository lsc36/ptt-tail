"""Decorator for hooks to activate if message matches any of given keywords."""
def keyword_match(*kwlist):
    def _deco(func):
        def _wrap(time, ptype, user, msg):
            if any(kw in msg for kw in kwlist):
                return func(time, ptype, user, msg)
        return _wrap
    return _deco
