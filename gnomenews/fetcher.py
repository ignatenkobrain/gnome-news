# Copyright (C) 2015 Igor Gnatenko <ignatenko@src.gnome.org>
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

from gi.repository import GObject, Grss

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class Fetcher(GObject.GObject):

    @log
    def __init__(self, channels=[]):
        """

        Args:
            channels (list): list of channels to fetch
        """
        GObject.GObject.__init__(self)
        self._pool = Grss.FeedsPool.new()
        self._pool.connect('feed-ready', self.on_feed_ready)
        self._pool.switch(True)
        self._channels = channels

    @log
    def add_channel(self, uri):
        """Add channel to fetcher

        Args:
            uri (str): URI of feed
        """
        self._channels.append(Grss.FeedChannel.new_with_source(uri))
        self._pool.listen(self._channels)

    @log
    def on_feed_ready(self, pool, feed, items):
        for item in items:
            print(item.get_title())
