from typing import Any
from datetime import datetime, timedelta
from src.core import logger


class KeyExpiredError(KeyError):
    pass


def __hax():
    class NoArg:
        pass
    return NoArg()


NoArg = __hax()


class DataCache():
    def __init__(
            self,
            default_expire_time: timedelta = timedelta(seconds=10),
            process_expires: bool = True
    ) -> None:
        self.__default_expire_time = default_expire_time
        self.__process_expires = process_expires
        self.__cache: dict[Any, Any] = {}

    def __getitem__(self, key: Any):
        c = self.__cache[key]

        n = datetime.now()
        if ((n - c['timestamp']) < c['expire_time']
           or not self.__process_expires):
            return c['data']

        del self.__cache[key]

        logger.debug("DataCache: Key %s expired" % repr(key))

        raise KeyExpiredError(key)

    def __contains__(self, key: Any):
        try:
            self.__cache[key]
            return True
        except KeyError:
            return False

    def __setitem__(self, key: Any, val: Any):
        self.__cache[key] = {
            'data': val,
            'timestamp': datetime.now(),
            'expire_time': self.__default_expire_time,
            }

    def __len__(self):
        return len(self.__cache)

    def items(self):
        keys = list(self.__cache)
        for k in keys:
            try:
                val = self.__cache[k]
                yield (k, val)
            except (KeyExpiredError, KeyError):
                pass

    def get(self, key: Any, default: Any = NoArg, expired: Any = NoArg):
        try:
            return self[key]
        except KeyExpiredError:
            if expired is NoArg and default is not NoArg:
                return default
            if expired is NoArg:
                return None
            return expired
        except KeyError:
            if default is NoArg:
                return None
            return default

    def set(self, key: Any, val: Any, expire_time: timedelta | None = None):
        if expire_time is None:
            expire_time = self.__default_expire_time

        self.__cache[key] = {
            'data': val,
            'timestamp': datetime.now(),
            'expire_time': expire_time,
            }

    def tryremove(self, key: Any) -> bool:
        if key in self.__cache:
            del self.__cache[key]
            return True
        return False

    def set_process_expires(self, value: bool) -> None:
        self.__process_expires = value

    def get_total_expire_time(self, key: Any) -> datetime:
        """Get the total amount of time the key will be in the cache for"""
        c = self.__cache[key]
        return c['expire_time']

    def get_expiration_time(self, key: Any) -> datetime:
        """Return the datetime when the given key will expire"""
        c = self.__cache[key]
        return c['timestamp'] + c['expire_time']

    def get_time_remaining(self, key: Any) -> timedelta:
        """Get the time left until the item will expire"""
        return self.get_expiration_time(key) - datetime.now()

    def get_timestamp(self, key: Any) -> datetime:
        return self.__cache[key]['timestamp']


dc = DataCache()
