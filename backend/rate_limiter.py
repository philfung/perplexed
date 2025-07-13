import time
from collections import deque
import threading


class RateLimiter:
    def __init__(self, limit_tokens_per_minute):
        self.limit_tokens_per_minute = limit_tokens_per_minute
        self.tokens = deque()
        self.lock = threading.Lock()

    def record(self, num_tokens):
        cur_time = time.time()
        with self.lock:
            self.tokens.append((cur_time, num_tokens))

    def is_over_limit(self):
        cur_time = time.time()
        with self.lock:
            # Remove tokens older than one minute
            while self.tokens and cur_time - self.tokens[0][0] > 60:
                _, num_tokens = self.tokens.popleft()

            tokens_last_minute = 0
            # check how many tokens have been used in the last minute
            for _, num_tokens in self.tokens:
                tokens_last_minute += num_tokens

            return tokens_last_minute >= self.limit_tokens_per_minute


if __name__ == "__main__":
    rate_limiter = RateLimiter(100)

    print(f"is over limit 1: {rate_limiter.is_over_limit()}")
    rate_limiter.record(90)
    print(f"is over limit 2: {rate_limiter.is_over_limit()}")
    rate_limiter.record(10)
    print(f"is over limit 3: {rate_limiter.is_over_limit()}")
    rate_limiter.record(10)
    print(f"is over limit 4: {rate_limiter.is_over_limit()}")
    time.sleep(61)
    print(f"is over limit 5: {rate_limiter.is_over_limit()}")
