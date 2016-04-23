# Uncomment to enable pwntools debug mode
#from pwn import context
#context.log_level = 'debug'

user = 'obov'
passwd = 'sowsowqq'

# User-defined hooks to process pushes
# Call example: for hook in hooks[board][aid]: hook(time, type, user, msg)
# Use '*' for wildcard board/aid
def hello(a, b, c, d):
    print 'Hello', c

hooks = {
        '*': {
            '*': [
                hello,
                ]
            }
        }
