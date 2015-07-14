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

from gi.repository import Gtk, GObject, WebKit2

from gettext import gettext as _

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class GenericFeedsView(Gtk.Stack):

    __gsignals__ = {
        'open-article': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    @log
    def __init__(self, tracker, name, title=None, show_feedlist=False):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.name = name
        self.title = title

        self.flowbox = Gtk.FlowBox(
            max_children_per_line=2, homogeneous=True,
            activate_on_single_click=True)
        self.flowbox.connect('child-activated', self._child_activated)

        self.feedlist = Gtk.ListBox()

        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if show_feedlist:
            self._box.pack_start(self.feedlist, True, True, 0)
        self._box.pack_end(self.flowbox, True, True, 0)
        self.add(self._box)

        self.tracker = tracker

        self.show_all()

    def _add_a_new_preview(self, post):
        url = post[0]
        title = post[1]
        date = post[2]
        author = post[3]
        text = post[4]

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_label = Gtk.Label(label=title)
        box.pack_start(title_label, False, False, 0)

        info_label = Gtk.Label(label=_("by %s at %s" % (author, date)))
        box.pack_start(info_label, False, False, 0)

        webview = WebKit2.WebView()
        webview.load_html(text)
        box.pack_end(webview, True, True, 0)

        #Store the post object to refer to it later on
        box.post = [url, title, author, text]

        self.flowbox.insert(box, -1)

    def _add_new_feed(self, url):
        self.feedlist.insert(Gtk.Label(url), -1)

    def _child_activated(self, box, child, user_data=None):
        post = child.get_children()[0].post
        self.emit('open-article', post)

    def update_items(self, _=None):
        posts = self.tracker.get_post_sorted_by_date(10)
        for post in posts:
            self._add_a_new_preview(post)
        self.show_all()

    def update_feeds(self, _=None):
        feeds = self.tracker.get_all_subscribed_feeds()
        for feed in feeds:
            self._add_new_feed(feed[0])
        self.show_all()


class FeedView(Gtk.Stack):
    def __init__(self, text_content):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        webview = WebKit2.WebView()
        webview.load_html(text_content)
        self.add(webview)
        self.show_all()

    def _back_button_clicked(self, widget):
        self.set_visible_child(view)


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
