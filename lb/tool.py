import functools
def log(f):
    @functools.wraps(f)
    def fn(*args, **argskw):
        print 'call lb.%s' % (f.__name__, )
        return f(*args, **argskw)
    return fn

log_list = []
