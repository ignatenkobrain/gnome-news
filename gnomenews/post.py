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

from gi.repository import WebKit2, GObject

from gnomenews import log
import logging
logger = logging.getLogger(__name__)

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
        self.author = cursor['fullname']

        self.webview = WebKit2.WebView(sensitive=False)
        self.webview.connect('load-changed', self._draw_thumbnail)

        self._generate_thumbnail()

    @log
    def _generate_thumbnail(self):
        self.webview.load_html("""
            <div style="width: 256px; height: 256px;">
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
            self.thumbnail = self.webview.get_snapshot_finish(res)
            self.emit('info-updated', self)
        except Exception:
            logger.error("Could not draw thumbnail for: " % self.title)
