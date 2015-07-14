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

from gi.repository import Gtk, Gio, GLib
from gettext import gettext as _

from gnomenews.toolbar import Toolbar, ToolbarState
from gnomenews.fetcher import Fetcher
from gnomenews.tracker import TrackerRSS
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

        self.fetcher = Fetcher()
        self.tracker = TrackerRSS()
        self.fetcher.connect('new-item', self.tracker.new_feed_item_signal)

        self.restore_saved_size()
        # Start drawing UI
        self._setup_view()

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
        self.connect("window-state-event", self._on_window_state_event)
        self.configure_event_handler = self.connect("configure-event", self._on_configure_event)

    def _on_window_state_event(self, widget, event):
        self.settings.set_boolean('window-maximized', 'GDK_WINDOW_STATE_MAXIMIZED' in event.new_window_state.value_names)

    def _on_configure_event(self, widget, event):
        with self.handler_block(self.configure_event_handler):
            GLib.idle_add(self._store_window_size_and_position, widget, priority=GLib.PRIORITY_LOW)

    def _store_window_size_and_position(self, widget):
        size = widget.get_size()
        self.settings.set_value('window-size', GLib.Variant('ai', [size[0], size[1]]))

        position = widget.get_position()
        self.settings.set_value('window-position', GLib.Variant('ai', [position[0], position[1]]))

    @log
    def _setup_view(self):
        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.views = []
        self.toolbar = Toolbar(self)
        self._stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.CROSSFADE,
            transition_duration=100,
            visible=True,
            can_focus=False)
        self._overlay = Gtk.Overlay(child=self._stack)
        self.set_titlebar(self.toolbar.header_bar)
        self._box.pack_start(self._overlay, True, True, 0)
        self.add(self._box)

        self._add_views()

        self.show_all()
        self.toolbar._back_button.set_visible(False)

    @log
    def _add_views(self):
        self.views.append(view.NewView(self.tracker))
        self.views.append(view.FeedsView(self.tracker))
        self.views.append(view.StarredView(self.tracker))
        self.views.append(view.ReadView(self.tracker))

        for i in self.views:
            if i.title:
                self._stack.add_titled(i, i.name, i.title)
            else:
                self._stack.add_named(i, i.name)
            i.connect('open-article', self.toolbar._open_article_view)

        self.views.append(view.SearchView(self.tracker))

        self.toolbar.set_stack(self._stack)
        self._stack.set_visible_child(self.views[0])

        self.fetcher.connect('items-updated', self.views[0].update_items)

    @log
    def _open_article_view(self, text_content):
        self.feed_view = view.FeedView(text_content)
        self._stack.previous_view = self._stack.get_visible_child()
        self._stack.add_named(self.feed_view, 'feedview')
        self._stack.set_visible_child(self.feed_view)

    @log
    def on_back_button_clicked(self, widget):
        self._stack.set_visible_child(self._stack.previous_view)
        self._stack.previous_view = None
        self._stack.remove(self.feed_view)
        self.feed_view = None
        self.toolbar.set_state(ToolbarState.MAIN)
