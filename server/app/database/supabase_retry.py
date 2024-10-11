import time
from functools import wraps

def retry_on_temporary_unavailable(max_retries=5, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "Resource temporarily unavailable" in str(e) and retries < max_retries - 1:
                        retries += 1
                        time.sleep(delay)
                    else:
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator