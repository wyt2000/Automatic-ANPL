import os
import json
import pathlib
from utils import mkdir_no_override, mkdir_override

# Save the responses from GPT.
class Cache:

    def __init__(self, file_path='cache.json', clean=False):
        self.file_path = file_path
        if clean or not os.path.exists(file_path):
            self.data = {}
            return
        with open(file_path, 'r') as f:
            self.data = json.loads(f.read())

    @staticmethod
    def get_key(*args):
        return str(tuple(args))

    def save(self, responses, *args):
        self.data[Cache.get_key(*args)] = responses

    def load(self, *args):
        return self.data.get(self.get_key(*args))

    def dump(self):
        with open(self.file_path, 'w') as f:
            f.write(json.dumps(self.data))

# Wrapped dict to create Cache object automatically.
class CacheContainer(dict):

    def __init__(self, prefix_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix_path = prefix_path

    def __missing__(self, task_kind):
        cache = Cache(pathlib.Path(self.prefix_path, f'{task_kind}.json'), True)
        self[task_kind] = cache
        return cache

# Map different kinds of GPT request to different cache files.
class CacheManager:

    def __init__(self, prefix_path='cache/', clean=False):
        self.prefix_path = prefix_path
        self.caches = CacheContainer(prefix_path)
        if clean:
            mkdir_override(prefix_path)
            return
        cache_paths = pathlib.Path(prefix_path).glob('*.json')
        for cache_path in cache_paths:
            self.caches[cache_path.stem] = Cache(cache_path, clean)

    def save(self, task_kind, responses, *args):
        self.caches[task_kind].save(responses, *args)

    def load(self, task_kind, *args):
        if (cache := self.caches.get(task_kind)) is not None:
            return cache.load(*args) 
        return None
        
    def __enter__(self):
        return self

    def __exit__(self, *args):
        mkdir_no_override(self.prefix_path)
        for cache in self.caches.values():
            cache.dump()

