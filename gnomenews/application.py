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
from gnomenews.about import AboutDialog

import os
import os.path

CACHE_PATH = "~/.cache/gnome-news"


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
        self._about_dialog = None

        delete_action = Gio.SimpleAction.new('delete_channel', parameter_type=GLib.VariantType.new('i'))
        self.add_action(delete_action)

        self.create_cache()

    @log
    def create_cache(self):
        cache_full_path = os.path.expanduser(CACHE_PATH)
        if not os.path.isdir(cache_full_path):
            os.mkdir(cache_full_path)

    @log
    def do_startup(self):
        Gtk.Application.do_startup(self)

    @log
    def quit(self, action=None, param=None):
        self._window.destroy()

    @log
    def about(self, action, param):
        def on_destroy(window):
            self._about_dialog = None

        if not self._about_dialog:
            self._about_dialog = AboutDialog(self)

        self._about_dialog.connect("destroy", on_destroy)
        self._about_dialog.present()

    def do_activate(self):
        if not self.get_app_menu():
            builder = Gtk.Builder()
            builder.add_from_resource("/org/gnome/News/Menu.ui")
            menu = builder.get_object("app-menu")
            self.set_app_menu(menu)
            for action_name in ["about", "quit"]:
                action = Gio.SimpleAction.new(action_name, None)
                action.connect("activate", getattr(self, action_name))
                self.add_action(action)

        if not self._window:
            self._window = Window(self)

        self._window.present()
