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


class NewView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'new', _("New"))

        # Insert some fake data
        for x in range(0, 10):
            self._add_new_item_with_url('http://new%d' % x)


class FeedsView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'feeds', _("Feeds"), show_feedlist=True)
        # Insert some fake data
        for x in range(0, 10):
            self._add_new_item_with_url('http://feeds%d' % x)

        # Add some fake feeds
        for x in range(0, 10):
            self.feedlist.insert(Gtk.Label('test%d' % x), -1)


class StarredView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'starred', _("Starred"))
        # Insert some fake data
        for x in range(0, 10):
            self._add_new_item_with_url('http://starred%d' % x)


class ReadView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'read', _("Read"))
        # Insert some fake data
        for x in range(0, 10):
            self._add_new_item_with_url('http://read%d' % x)


class SearchView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'search')
