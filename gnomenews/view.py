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

from gi.repository import Gtk, GObject, WebKit2, GLib, Gdk

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
            activate_on_single_click=True,
            row_spacing=10, column_spacing=10,
            margin=15,
            selection_mode=Gtk.SelectionMode.NONE)
        self.flowbox.get_style_context().add_class('feeds-list')
        self.flowbox.connect('child-activated', self._post_activated)

        self.feed_stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.CROSSFADE,
            transition_duration=100,
            visible=True,
            can_focus=False)

        self.stacksidebar = Gtk.StackSidebar(
            visible=True,
            stack=self.feed_stack)

        self._box = Gtk.Box(
            valign=Gtk.Align.START,
            orientation=Gtk.Orientation.VERTICAL)

        if show_feedlist:
            self._box.set_orientation(Gtk.Orientation.HORIZONTAL)
            self._box.pack_start(self.stacksidebar, True, True, 0)
            self._box.pack_end(self.feed_stack, True, True, 0)
        else:
            self._box.pack_end(self.flowbox, True, True, 0)

        scrolledWindow.add(self._box)

        self.tracker = tracker
        self.show_all()

    @log
    def _add_a_new_preview(self, cursor, child=None):
        p = Post(cursor)
        if child:
            p.flowbox = child
        else:
            p.flowbox = self.flowbox
        p.connect('info-updated', self._insert_post)

    @log
    def _insert_post(self, source, post):
        image = Gtk.Image.new_from_file(post.thumbnail)
        image.get_style_context().add_class('feed-box')
        image.show_all()

        #Store the post object to refer to it later on
        image.post = post.cursor

        source.flowbox.insert(image, -1)

    @log
    def _add_new_feed(self, feed):
        flowbox = Gtk.FlowBox(
            min_children_per_line=2,
            activate_on_single_click=True,
            row_spacing=10, column_spacing=10,
            margin=15,
            selection_mode=Gtk.SelectionMode.NONE)
        flowbox.get_style_context().add_class('feeds-list')
        flowbox.connect('child-activated', self._post_activated)
        flowbox.show()
        posts = self.tracker.get_posts_for_channel(feed['url'], 10)
        [self._add_a_new_preview(post, flowbox) for post in posts]

        if not feed['title']:
            feed['title'] = _("Unknown feed")
        self.feed_stack.add_titled(flowbox, feed['url'], feed['title'])

    @log
    def _post_activated(self, box, child, user_data=None):
        post = child.get_children()[0].post
        self.emit('open-article',
                  post['title'], post['fullname'], post['url'], post["content"])

    @log
    def update_new_items(self, _=None):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        posts = self.tracker.get_post_sorted_by_date(10, unread=True)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_read_items(self):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        posts = self.tracker.get_post_sorted_by_date(10, read_only=True)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_starred_items(self):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        posts = self.tracker.get_post_sorted_by_date(10, starred=True)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

    @log
    def update_feeds(self, _=None):
        feeds = self.tracker.get_channels()
        for new_feed in feeds:
            if not self.feed_stack.get_child_by_name(new_feed['url']):
                self._add_new_feed(new_feed)

    @log
    def update(self):
        pass


class FeedView(Gtk.Stack):

    __gsignals__ = {
        'post-read': (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self, tracker, url, contents):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        webview = WebKit2.WebView()
        if contents:
            webview.load_html("""
            <style>
              article {
                overflow-y: hidden;
                margin: 20px auto;
                width: 600px;
                color: #333;
                font-family: Cantarell;
                font-size: 18px;
              }
            </style>
            <body>
              <article>%s</article>
            </body>
            """ % contents)
        webview.connect("decide-policy", self._on_webview_decide_policy)
        self.add(webview)
        self.show_all()

        self.url = url

        GLib.timeout_add(1000, self.mark_post_as_read)

    @staticmethod
    @log
    def _on_webview_decide_policy(web_view, decision, decision_type):
        uri = decision.get_request().get_uri()
        if uri == "about:blank":
            decision.use()
            return False
        else:
            # it's external link
            decision.ignore()
            Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)
            return True

    def mark_post_as_read(self):
        self.emit('post-read', self.url)
        return False


class NewView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'new', _("New"))

    @log
    def update(self):
        self.update_new_items()


class FeedsView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'feeds', _("Feeds"), show_feedlist=True)

    @log
    def update(self):
        self.update_feeds()


class StarredView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'starred', _("Starred"))

    @log
    def update(self):
        self.update_starred_items()


class ReadView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'read', _("Read"))

    @log
    def update(self):
        self.update_read_items()


class SearchView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'search')
