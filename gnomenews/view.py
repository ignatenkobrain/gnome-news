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

from gi.repository import Gtk, GObject, WebKit2, GLib

from gettext import gettext as _

from gnomenews import log
from gnomenews.post import Post
import logging
logger = logging.getLogger(__name__)


class GenericFeedsView(Gtk.Stack):

    __gsignals__ = {
        'open-article': (GObject.SignalFlags.RUN_FIRST, None, (str, str, str, str)),
    }

    @log
    def __init__(self, tracker, name, title=None, show_feedlist=False):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.name = name
        self.title = title

        scrolledWindow = Gtk.ScrolledWindow()
        self.add(scrolledWindow)

        self.flowbox = Gtk.FlowBox(
            min_children_per_line=2,
            max_children_per_line=4, homogeneous=True,
            activate_on_single_click=True,
            row_spacing=10, column_spacing=10,
            margin=15,
            selection_mode=Gtk.SelectionMode.NONE)
        self.flowbox.get_style_context().add_class('feeds-list')
        self.flowbox.connect('child-activated', self._post_activated)

        self.feedlist = Gtk.ListBox(
            activate_on_single_click=True)
        self.feedlist.get_style_context().add_class('channel-list')
        self.feedlist.connect('row-activated', self._feed_activated)

        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if show_feedlist:
            self._box.pack_start(self.feedlist, False, True, 0)
        self._box.pack_end(self.flowbox, True, True, 0)
        scrolledWindow.add(self._box)

        self.tracker = tracker

        self.show_all()

    @log
    def _add_a_new_preview(self, cursor):
        p = Post(cursor)
        p.connect('info-updated', self._insert_post)

    def _insert_post(self, source, post):
        image = Gtk.Image.new_from_surface(post.thumbnail)
        image.get_style_context().add_class('feed-box')
        image.show_all()

        #Store the post object to refer to it later on
        image.post = post.cursor

        self.flowbox.insert(image, -1)

    @log
    def _add_new_feed(self, feed):
        label = Gtk.Label(label=feed['title'])
        label.channel = feed['url']
        label.get_style_context().add_class('channel')
        self.feedlist.insert(label, -1)

    @log
    def _post_activated(self, box, child, user_data=None):
        post = child.get_children()[0].post
        self.emit('open-article',
                  post['title'], post['fullname'], post['url'], post["content"])

    @log
    def _feed_activated(self, box, child, user_data=None):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        url = child.get_child().channel
        posts = self.tracker.get_posts_for_channel(url, 10)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_new_items(self):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        posts = self.tracker.get_post_sorted_by_date(10, unread=True)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_all_items(self):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        posts = self.tracker.get_post_sorted_by_date(10, unread=False)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_starred_items(self):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        posts = self.tracker.get_post_sorted_by_date(10, unread=False, starred=True)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_feeds(self, _=None):
        [self.feedlist.remove(old_feed) for old_feed in self.feedlist.get_children()]

        feeds = self.tracker.get_channels()
        [self._add_new_feed(feed) for feed in feeds]
        if len(self.feedlist.get_children()) > 0:
            self._feed_activated(None, self.feedlist.get_children()[0])
        self.show_all()


class FeedView(Gtk.Stack):

    __gsignals__ = {
        'post-read': (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self, tracker, url, contents):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        webview = WebKit2.WebView()
        if contents:
            webview.load_html(contents)
        self.add(webview)
        self.show_all()

        self.url = url

        GLib.timeout_add(1000, self.mark_post_as_read)

    def mark_post_as_read(self):
        self.emit('post-read', self.url)
        return False


class NewView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'new', _("New"))
        self.update_new_items()


class FeedsView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'feeds', _("Feeds"), show_feedlist=True)
        self.update_feeds()


class StarredView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'starred', _("Starred"))
        self.update_starred_items()


class ReadView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'read', _("Read"))
        self.update_starred_items()


class SearchView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'search')
