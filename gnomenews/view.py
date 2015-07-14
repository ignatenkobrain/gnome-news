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

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class GenericFeedsView(Gtk.Stack):

    @log
    def __init__(self, tracker, name, title=None, show_feedlist=False):
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

        self.tracker = tracker

        self.show_all()

    def _add_new_item_with_url(self, url, text_contents):
        webview = WebKit2.WebView()
        webview.load_html(text_contents)
        self.flowbox.insert(webview, -1)

    def _add_new_feed(self, url):
        self.feedlist.insert(Gtk.Label(url), -1)

    def update_items(self, _=None):
        posts = self.tracker.get_post_sorted_by_date(10)
        for post in posts:
            self._add_new_item_with_url(post[0], post[3])
        self.show_all()

    def update_feeds(self, _=None):
        feeds = self.tracker.get_all_subscribed_feeds()
        for feed in feeds:
            self._add_new_feed(feed[0])
        self.show_all()


class NewView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'new', _("New"))
        self.update_feeds()


class FeedsView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'feeds', _("Feeds"), show_feedlist=True)
        self.update_feeds()


class StarredView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'starred', _("Starred"))
        self.update_feeds()


class ReadView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'read', _("Read"))
        self.update_feeds()


class SearchView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'search')
