from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from typing import Union

import plyvel

from mowgli.lib.storage._closeable import _Closeable


class _Leveldb(_Closeable):
    def __init__(self, *, name: Union[str, Path], create_if_missing=True, delete_on_close=False, **kwds):
        self._db = plyvel.DB(name=str(name), create_if_missing=create_if_missing, **kwds)
        self.__delete_on_close = delete_on_close
        self.__name = name

    def close(self):
        self._db.close()
        if self.__delete_on_close:
            rmtree(self.__name)

    @property
    def closed(self):
        return self._db.closed

    @classmethod
    def temporary(cls):
        return cls(name=mkdtemp(), delete_on_close=True)
