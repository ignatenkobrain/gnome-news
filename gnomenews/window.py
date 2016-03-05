# Copyright (C) 2015 Vadim Rutkovsky <vrutkovs@redhat.com>
# Copyright (C) 2015 Igor Gnatenko <ignatenko@src.gnome.org>
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

from gi.repository import Gtk, Gio, GLib, GObject
from gettext import gettext as _

from gnomenews.toolbar import Toolbar, ToolbarState
from gnomenews.tracker import Tracker
from gnomenews import view

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class Window(Gtk.ApplicationWindow):

    @log
    def __init__(self, app):
        Gtk.ApplicationWindow.__init__(self,
                                       application=app,
                                       title=_("News"))
        self.settings = Gio.Settings.new('org.gnome.News')
        self.set_size_request(200, 100)
        self.set_icon_name('gnome-news')

        self.tracker = Tracker()

        self.restore_saved_size()

        # Setup UI widgets
        self._setup_widgets()

        self.show()

    @log
    def restore_saved_size(self):

        # Restore window size from gsettings
        size_setting = self.settings.get_value('window-size')
        if isinstance(size_setting[0], int) and isinstance(size_setting[1], int):
            self.resize(size_setting[0], size_setting[1])

        position_setting = self.settings.get_value('window-position')
        if len(position_setting) == 2 \
           and isinstance(position_setting[0], int) \
           and isinstance(position_setting[1], int):
            self.move(position_setting[0], position_setting[1])

        if self.settings.get_value('window-maximized'):
            self.maximize()

        # Save changes to window size
        self.connect("key-press-event", self._on_key_press_event)
        self.connect("window-state-event", self._on_window_state_event)
        self.configure_event_handler = self.connect("configure-event", self._on_configure_event)

    def _on_window_state_event(self, widget, event):
        self.settings.set_boolean('window-maximized', 'GDK_WINDOW_STATE_MAXIMIZED' in event.new_window_state.value_names)

    def _on_configure_event(self, widget, event):
        with self.handler_block(self.configure_event_handler):
            GLib.idle_add(self._store_window_size_and_position, widget, priority=GLib.PRIORITY_LOW)

    def _on_key_press_event(self, widget, event):
        return self.search_bar.handle_event(event)

    def _store_window_size_and_position(self, widget):
        size = widget.get_size()
        self.settings.set_value('window-size', GLib.Variant('ai', [size[0], size[1]]))

        position = widget.get_position()
        self.settings.set_value('window-position', GLib.Variant('ai', [position[0], position[1]]))

    @log
    def _setup_widgets(self):
        self._ui = Gtk.Builder()
        self._ui.add_from_resource('/org/gnome/News/ui/window.ui')

        self._box = self._ui.get_object('box')
        self.add(self._box)

        # Views
        self.views = []
        self._stack = self._ui.get_object('stack')
        self._overlay = self._ui.get_object('overlay')
        self._stack.connect("notify::visible-child", self.view_changed)

        # Action bar
        self.action_bar = self._ui.get_object('action_bar')

        # Search bar
        self.search_bar = self._ui.get_object('search_bar')
        self.search_entry = self._ui.get_object('search_entry')

        self.search_entry.connect('search-changed', self.on_search_changed)

        # Header bar
        self.toolbar = Toolbar(self)
        self.set_titlebar(self.toolbar.header_bar)

        self._add_views()

        self.toolbar._back_button.set_visible(False)

    @log
    def view_changed(self, stack, property_name):
        visible_view = self._stack.get_visible_child()
        if visible_view in self.views:
            visible_view.update()

    @log
    def _add_views(self):
        self.views.append(view.NewView(self.tracker))
        self.views.append(view.FeedsView(self.tracker))
        self.views.append(view.StarredView(self.tracker))

        for i in self.views:
            if i.title:
                self._stack.add_titled(i, i.name, i.title)
            else:
                self._stack.add_named(i, i.name)
            i.connect('open-article', self.toolbar._update_title)

        self.views.append(view.SearchView(self.tracker))

        self.toolbar.set_stack(self._stack)
        self._stack.set_visible_child(self.views[0])

        # Search view
        self.search_view = view.SearchView(self.tracker)

        self.search_entry.bind_property('text', self.search_view, 'search-query',
                                        GObject.BindingFlags.BIDIRECTIONAL)

        self.tracker.connect('items-updated', self.views[0].update_new_items)
        self.tracker.connect('feeds-updated', self.views[1].update_feeds)

    @log
    def _open_article_view(self, post):
        self.feed_view = view.FeedView(self.tracker, post)
        self._stack.previous_view = self._stack.get_visible_child()
        self._stack.add_named(self.feed_view, 'feedview')
        self._stack.set_visible_child(self.feed_view)
        self.tracker.post_read_signal = self.feed_view.connect('post-read', self.tracker.mark_post_as_read)

    @log
    def on_back_button_clicked(self, widget):
        self._stack.set_visible_child(self._stack.previous_view)
        self._stack.previous_view = None
        self._stack.remove(self.feed_view)
        self.toolbar.set_state(ToolbarState.MAIN)
        self.feed_view.disconnect(self.tracker.post_read_signal)
        self.feed_view = None

    @log
    def on_search_changed(self, entry, data=None):
        if entry.get_text_length() > 0:
            # Add the view if it's not added yet
            if self.search_view not in self._stack.get_children():
                self._stack.previous_view = self._stack.get_visible_child()
                self._stack.add_named(self.search_view, 'search_view')

            self._stack.set_visible_child(self.search_view)
        else:
            self._stack.set_visible_child(self._stack.previous_view)
            self._stack.previous_view = None
            self._stack.remove(self.search_view)
