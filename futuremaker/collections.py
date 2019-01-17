import threading
import time


class expiredict(dict):
    # 10분..?
    def __init__(self, expire_time=5, expired_callback=None):
        self.expire_time = expire_time
        self.expire_dict = dict()
        self.is_look = False

        def checker():
            while True:
                if not self.is_look:
                    try:
                        now = time.time()
                        keys = self.expire_dict.keys()
                        for key in keys:
                            try:
                                val = self.expire_dict[key]
                                diff = now - val
                                if diff > self.expire_time:
                                    val = self[key]
                                    del self[key]
                                    del self.expire_dict[key]
                                    if expired_callback is not None:
                                        expired_callback(val)
                            except KeyError:
                                del self.expire_dict[key]
                    except RuntimeError:
                        # 돌고돌고..
                        pass

        threading.Thread(target=checker, daemon=True).start()

    def __setitem__(self, key, value):
        self.expire_dict[key] = time.time()
        return dict.__setitem__(self, key, value)

    def __getitem__(self, item):
        return dict.__getitem__(self, item)

    def lock(self):
        self.is_look = True

    def unlook(self):
        self.is_look = False