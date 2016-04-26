# Copyright (C) 2015 Felipe Borges <felipeborges@gnome.org>
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

from gi.repository import WebKit2, GObject, GLib

import hashlib
import os.path
import re

from gnomenews import log
from gnomenews.application import CACHE_PATH
import logging
logger = logging.getLogger(__name__)

THUMBNAIL_WIDTH = 256
THUMBNAIL_HEIGHT = 256

NAME_REGEX = re.compile("\(([^\)]+)\)")


class Post(GObject.GObject):

    __gsignals__ = {
        'info-updated': (GObject.SignalFlags.RUN_FIRST, None, (GObject.GObject,)),
    }

    @log
    def __init__(self, cursor):
        GObject.GObject.__init__(self)

        self.cursor = cursor

        self.title = cursor['title']
        self.content = cursor['content']
        self.url = cursor['url']
        self.is_read = cursor['is_read']
        self.is_starred = cursor['is_starred']

        self.author = self.sanitize_author(cursor['fullname'])
        self.author_email = cursor['author_email']
        self.author_homepage = cursor['author_homepage']

        # Check cache first
        hashed_url = hashlib.md5(cursor['url'].encode()).hexdigest()
        self.cached_thumbnail_path = os.path.join(CACHE_PATH, '%s.png' % hashed_url)

        GLib.idle_add(self.try_to_load_image_from_cache)

    @staticmethod
    @log
    def sanitize_author(author):
        """Separates Name from Email in an author string

        RSS 2.0 from https://planet.gnome.org/rss20.xml returns
        "me@example.com - (Firstname Lastname)" as author fiels. This is a
        workaround for it.

        TODO: fix this hack in pluggable methods or in libgrss

        Args:
            author (str): an author string extracted from a rss feed
        """
        try:
            return re.findall(NAME_REGEX, author)[0]
        except:
            return author

    @log
    def try_to_load_image_from_cache(self):
        if os.path.isfile(self.cached_thumbnail_path):
            self.thumbnail = self.cached_thumbnail_path
            self.emit('info-updated', self)
        else:
            self.webview = WebKit2.WebView(sensitive=False)
            self.webview.connect('load-changed', self._draw_thumbnail)
            self._generate_thumbnail()

    @log
    def _generate_thumbnail(self):
        self.webview.load_html("""
            <div style="width: 250px">
                <h3 style="margin-bottom: 2px">%s</h3>
                <small style="color: #333">%s</small>
                <small style="color: #9F9F9F">%s</small>
            </div>""" % (self.title, self.author, self.content))

    @log
    def _draw_thumbnail(self, webview, event):
        if event == WebKit2.LoadEvent.FINISHED:
            self.webview.get_snapshot(WebKit2.SnapshotRegion.FULL_DOCUMENT,
                                      WebKit2.SnapshotOptions.NONE,
                                      None, self._save_thumbnail, None)

    @log
    def _save_thumbnail(self, webview, res, data):
        try:
            original_surface = self.webview.get_snapshot_finish(res)

            import cairo
            new_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
            ctx = cairo.Context(new_surface)
            ctx.set_source_surface(original_surface, 0, 0)
            ctx.paint()

            new_surface.write_to_png(self.cached_thumbnail_path)

            self.thumbnail = self.cached_thumbnail_path
            self.emit('info-updated', self)
        except Exception as e:
            logger.error("Could not draw thumbnail for %s: %s" % (self.title, str(e)))
