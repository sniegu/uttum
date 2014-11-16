from __future__ import print_function
import sys

from . exceptions import UttumException, SentryException
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

        try:
            from . import checking
            self._status = checking.check_all()
            for s in self._status:
                s["instance"] = str(id(self)) + "_" + s["name"]
        except SentryException as e:
            self._status = [dict(color='#ff0000', full_text='uttum', name='uttum')]
        except UttumException as e:
            self._status = [dict(color='#ff0000', full_text='uttum: %s' % e, name='uttum')]



