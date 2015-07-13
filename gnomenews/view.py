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

from gi.repository import Gtk, WebKit

from gettext import gettext as _

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class GenericFeedsView(Gtk.Stack):

    @log
    def __init__(self, name, title=None):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.name = name
        self.title = title

        self.webview = WebKit.WebView()

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.webview)

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._box.pack_start(scrolled_window, True, True, 0)
        self.add(self._box)

        self.show_all()


class NewView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'new', _("New"))
        self.webview.load_uri('http://new')


class FeedsView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'feeds', _("Feeds"))
        self.webview.load_uri('http://feeds')


class StarredView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'starred', _("Starred"))
        self.webview.load_uri('http://starred')


class ReadView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'read', _("Read"))
        self.webview.load_uri('http://read')


class SearchView(GenericFeedsView):
    def __init__(self):
        GenericFeedsView.__init__(self, 'search')
