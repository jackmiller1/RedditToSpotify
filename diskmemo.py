import pickle
import os

## Persistantly memoizes a function.
## Loads and saves the cache dictionary to file
## Must call save_cache to save the cache to file
class DiskMemoize:
    def __init__(self, cache_file, cache_filter=lambda t: True):
        self.cache_file = cache_file
        self.cache_filter = cache_filter
        if os.path.isfile(self.cache_file):
            with open(self.cache_file, 'rb') as f:
                self.cache = pickle.load(f)
        else:
            self.cache = {}

    def __call__(self, func):
        def wrapper(instance, *args, **kwargs):
            if args not in self.cache:
                val = func(instance, *args, **kwargs)
                if self.cache_filter(val):
                    self.cache[args] = val
                else:
                    return val
            return self.cache[args]
        return wrapper

    def save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f, pickle.HIGHEST_PROTOCOL)