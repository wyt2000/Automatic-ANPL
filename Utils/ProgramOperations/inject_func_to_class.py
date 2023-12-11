__all__ = ['inject_func_to_class']

def inject_func_to_class(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator