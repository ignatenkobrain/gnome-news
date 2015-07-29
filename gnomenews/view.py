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

from gi.repository import Gtk, GObject, WebKit2, GLib, Gdk, Gio

from gettext import gettext as _

from gnomenews import log
from gnomenews.post import Post
import logging
logger = logging.getLogger(__name__)


class GenericFeedsView(Gtk.Stack):

    __gsignals__ = {
        'open-article': (GObject.SignalFlags.RUN_FIRST, None, (GObject.GObject,)),
    }

    @log
    def __init__(self, tracker, name, title=None, show_feedlist=False):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.name = name
        self.title = title

        self.flowbox = Gtk.FlowBox(
            min_children_per_line=2,
            activate_on_single_click=True,
            row_spacing=10, column_spacing=10,
            margin=15,
            valign=Gtk.Align.START,
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
        self.stacksidebar.set_size_request(200, -1)

        self.listbox = self.stacksidebar.get_children()[0].get_children()[0].get_children()[0]

        scrolledWindow = Gtk.ScrolledWindow()
        if show_feedlist:
            self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self._box.pack_start(self.stacksidebar, False, True, 0)
            sep = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
            self._box.pack_start(sep, False, True, 0)
            self._box.pack_start(scrolledWindow, True, True, 0)
            scrolledWindow.add(self.feed_stack)
            self.add(self._box)
        else:
            self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self._box.pack_end(self.flowbox, True, True, 0)
            scrolledWindow.add(self._box)
            self.add(scrolledWindow)

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

        # Store the post object to refer to it later on
        image.post = post.cursor

        source.flowbox.insert(image, -1)

    @log
    def _add_new_feed(self, feed):
        flowbox = Gtk.FlowBox(
            min_children_per_line=2,
            activate_on_single_click=True,
            row_spacing=10, column_spacing=10,
            valign=Gtk.Align.START,
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

        # Set URL as a tooltip
        self.listbox.get_children()[-1].get_child().set_tooltip_text(feed['url'])

    @log
    def _post_activated(self, box, child, user_data=None):
        cursor = child.get_children()[0].post
        post = Post(cursor)
        self.emit('open-article', post)

    @log
    def update_new_items(self, _=None):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        posts = self.tracker.get_post_sorted_by_date(10, unread=True)
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
        new_feeds = self.tracker.get_channels()
        new_feed_urls = [new_feed['url'] for new_feed in new_feeds]
        old_feed_urls = [child.get_child().get_tooltip_text() for child in self.listbox.get_children()]

        # Remove old feeds
        for url in old_feed_urls:
            if url not in new_feed_urls:
                logger.info("Removing channel %s" % url)
                self.feed_stack.remove(self.feed_stack.get_child_by_name(url))

        # Add new feeds
        for new_feed in new_feeds:
            if new_feed['url'] not in old_feed_urls:
                logger.info("Adding channel %s" % new_feed['url'])
                self._add_new_feed(new_feed)

    @log
    def update(self):
        pass


class FeedView(Gtk.Stack):

    __gsignals__ = {
        'post-read': (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self, tracker, post):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        stylesheet = Gio.File.new_for_uri('resource:///org/gnome/News/aboutReaderContent.css')
        webview = WebKit2.WebView()
        if post.content:
            html = """
                <style>%s</style>
                <body>
                  <article>
                  <h1>%s</h1>
                  <span>%s</span>
                  <p>%s</p>
                  <div id="footer">""" % (stylesheet.load_contents(None)[1].decode(), post.title, post.author, post.content)

            if post.author_homepage:
                html += """<p><a href="%s">%s</a></p>""" % post.author_homepage

            if post.author_email:
                html += """<p><a href="mailto:%s?Subject=%s">%s</a></p>""" % (post.author_email, post.title, post.author_email)

            html += """
            <p><a href="%s">View post</a></p>
            </div>
            </article>
            </body>
            """ % post.url

            webview.load_html(html)

        webview.connect("decide-policy", self._on_webview_decide_policy)
        self.add(webview)
        self.show_all()

        self.url = post.url

    @staticmethod
    @log
    def _on_webview_decide_policy(web_view, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_request().get_uri()
            if uri != "about:blank" and decision.get_navigation_type() == WebKit2.NavigationType.LINK_CLICKED:
                decision.ignore()
                try:
                    Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)
                except GLib.Error:
                    # for example, irc://irc.gimp.org/#guadec
                    logger.warning("Couldn't open URI: %s" % uri)
                return True
        return False

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

        self.listbox.connect('button-release-event', self._on_button_release)

        app = Gio.Application.get_default()
        delete_channel_action = app.lookup_action('delete_channel')
        delete_channel_action.connect('activate', self.delete_channel)

    @log
    def update(self):
        self.update_feeds()

    @log
    def _on_button_release(self, w, event):
        (_, button) = event.get_button()

        if button != Gdk.BUTTON_SECONDARY:
            return Gdk.EVENT_PROPAGATE

        try:
            selected_row = self.listbox.get_row_at_y(event.y)
            if selected_row:
                index = selected_row.get_index()

                menu = Gio.Menu()
                menu.append("Remove", "app.delete_channel(%s)" % index)

                popover = Gtk.Popover.new_from_model(selected_row, menu)
                popover.position = Gtk.PositionType.BOTTOM
                popover.show()

        except Exception as e:
            logger.warn("Error showing popover: %s" % str(e))

        return Gdk.EVENT_STOP

    @log
    def delete_channel(self, action, index_variant):
        try:
            index = index_variant.get_int32()
            row = self.listbox.get_children()[index]
            url = row.get_child().get_tooltip_text()
            self.tracker.remove_channel(url)
        except Exception as e:
            logger.warn("Failed to remove feed %s: %s" % (str(index_variant), str(e)))


class StarredView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'starred', _("Starred"))

    @log
    def update(self):
        self.update_starred_items()


class SearchView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'search')
