import threading


class QueryCache:
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()

    def get(self, key):
        value = None
        with self.lock:
            value = self.cache.get(key)
        return value

    def set(self, key, value):
        with self.lock:
            self.cache[key] = value

    def delete(self, key):
        with self.lock:
            self.cache.pop(key, None)

    def clear(self):
        with self.lock:
            self.cache = {}
