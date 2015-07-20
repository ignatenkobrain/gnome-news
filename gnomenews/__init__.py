# Copyright (C) 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from itertools import chain
import logging
import time
logger = logging.getLogger(__name__)
tabbing = 0


def log(fn):
    if logger.getEffectiveLevel() > logging.DEBUG:
        return fn

    def wrapped(*v, **k):
        global tabbing
        name = fn.__name__
        module = fn.__module__
        filename = fn.__code__.co_filename.split('/')[-1]
        lineno = fn.__code__.co_firstlineno
        params = ", ".join(map(repr, chain(v, k.values())))

        tabbing += 1
        start = time.time()
        retval = fn(*v, **k)
        elapsed = time.time() - start
        tabbing -= 1
        elapsed_time = ''
        if elapsed > 0.5:
            elapsed_time = ', took %02f' % elapsed
        logger.debug("%s:%s %s%s.%s(%s), returned %s%s",
                     filename, lineno, '|' * tabbing, module, name, params, retval, elapsed_time)

        return retval
    return wrapped
