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


from gi.repository import Gtk, GLib, Gio, Gdk
from gettext import gettext as _

from gnomenews import log
from gnomenews.window import Window


class Application(Gtk.Application):
    @log
    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id='org.gnome.News',
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        GLib.set_application_name(_("News"))
        GLib.set_prgname('gnome-news')
        self.settings = Gio.Settings.new('org.gnome.News')

        cssProviderFile = Gio.File.new_for_uri('resource:///org/gnome/News/application.css')
        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_file(cssProviderFile)
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self._window = None

    @log
    def do_startup(self):
        Gtk.Application.do_startup(self)

    @log
    def quit(self, action=None, param=None):
        self._window.destroy()

    def do_activate(self):
        if not self._window:
            self._window = Window(self)

        self._window.present()
