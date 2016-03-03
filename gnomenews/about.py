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

from gi.repository import Gtk, Gio


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self)
        self.parent = parent
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_artists(self._read_file("ARTISTS"))
        self.set_authors(self._read_file("AUTHORS"))
        self.set_copyright("Copyright © 2015 GNOME Foundation")
        self.set_license_type(Gtk.License.GPL_3_0)
        self.set_version(self._read_file("VERSION")[0])
        self.set_website("https://wiki.gnome.org/Design/Apps/Potential/News")
        self.set_logo_icon_name("gnome-news")

    @staticmethod
    def _read_file(fname):
        f = Gio.File.new_for_uri("resource:///org/gnome/News/%s" % fname)
        lines = f.load_contents(None)[1].decode().split("\n")
        # Drop lines which empty or starts with '#'
        lines_filtered = list(filter(lambda k: not k.startswith("#"), filter(None, lines)))
        return lines_filtered
