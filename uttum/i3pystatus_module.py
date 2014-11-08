from __future__ import print_function
import sys

from . import checking
from i3pystatus import IntervalModule
from i3pystatus.core.util import convert_position

class Uttum(IntervalModule):
    _status = None

    def init(self):
        pass

    def inject(self, json):
        if self._status:
            for s in self._status:
                json.insert(convert_position(0, json), s)


    def run(self):
        self._status = checking.check_all()
        for s in self._status:
            s["instance"] = str(id(self)) + "_" + s["name"]


