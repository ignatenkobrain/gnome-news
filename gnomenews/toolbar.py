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

from gi.repository import Gtk, GObject, GLib

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class ToolbarState:
    MAIN = 0
    CHILD_VIEW = 1
    SEARCH_VIEW = 2


class Toolbar(GObject.GObject):

    __gsignals__ = {
        'state-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    @log
    def __init__(self, window):
        GObject.GObject.__init__(self)
        self.window = window
        self._stack_switcher = Gtk.StackSwitcher(
            margin_top=2, margin_bottom=2, can_focus=False, halign="center")
        self._stack_switcher.show()
        self._ui = Gtk.Builder()
        self._ui.add_from_resource('/org/gnome/News/HeaderBar.ui')
        self.header_bar = self._ui.get_object('header-bar')
        self.header_bar.set_show_close_button(True)
        self.header_bar.set_custom_title(self._stack_switcher)

        self.add_toggle_button = self._ui.get_object('add-toggle-button')
        self.add_popover = self._ui.get_object('add-popover')
        self.add_popover.hide()
        self.add_toggle_button.set_popover(self.add_popover)

        self.new_url = self._ui.get_object('new-url')
        self.add_button = self._ui.get_object('add-button')
        self.add_button.connect('clicked', self._add_new_feed)

    @log
    def reset_header_title(self):
        self.header_bar.set_custom_title(self._stack_switcher)

    @log
    def set_stack(self, stack):
        self._stack_switcher.set_stack(stack)

    @log
    def get_stack(self):
        return self._stack_switcher.get_stack()

    @log
    def hide_stack(self):
        self._stack_switcher.hide()

    @log
    def show_stack(self):
        self._stack_switcher.show()

    @log
    def set_state(self, state, btn=None):
        self._state = state
        self._update()
        self.emit('state-changed')

    @log
    def _add_new_feed(self, button):
        new_url = self.new_url.get_text()
        GLib.idle_add(self.window.fetcher.add_channel, new_url)
        self.add_popover.hide()
