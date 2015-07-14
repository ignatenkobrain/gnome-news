# Copyright (C) 2015 Vadim Rutkovsky <vrutkovs@redhat.com>
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

from gi.repository import Gtk, WebKit2

from gettext import gettext as _

from gnomenews.tracker import TrackerRSS

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class GenericFeedsView(Gtk.Stack):

    tracker = TrackerRSS()

    @log
    def __init__(self, name, title=None, show_feedlist=False):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.name = name
        self.title = title

        self.flowbox = Gtk.FlowBox(
            max_children_per_line=2, homogeneous=True)

        self.feedlist = Gtk.ListBox()

        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if show_feedlist:
            self._box.pack_start(self.feedlist, True, True, 0)
        self._box.pack_end(self.flowbox, True, True, 0)
        self.add(self._box)

        self.show_all()

    def _add_new_item_with_url(self, url):
        webview = WebKit2.WebView()
        webview.load_uri(url)
        self.flowbox.insert(webview, -1)

    def _add_new_feed(self, url):
        self.feedlist.insert(Gtk.Label(url), -1)


class NewView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'new', _("New"))

        posts = self.tracker.get_post_sorted_by_date(10)
        for post in posts:
            self._add_new_item_with_url(post[0])


class FeedsView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'feeds', _("Feeds"), show_feedlist=True)

        posts = self.tracker.get_post_sorted_by_date(10)
        for post in posts:
            self._add_new_item_with_url(post[0])

        feeds = self.tracker.get_all_subscribed_feeds()
        for feed in feeds:
            self._add_new_feed([0])


class StarredView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'starred', _("Starred"))

        posts = self.tracker.get_post_sorted_by_date(10)
        for post in posts:
            self._add_new_item_with_url(post[0])


class ReadView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'read', _("Read"))

        posts = self.tracker.get_post_sorted_by_date(10)
        for post in posts:
            self._add_new_item_with_url(post[0])


class SearchView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'search')
