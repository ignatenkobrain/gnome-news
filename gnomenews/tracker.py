# Copyright (C) 2015 Igor Gnatenko <ignatenko@src.gnome.org>
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

from gi.repository import GObject, Gio, Tracker as Trackr

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class Tracker(GObject.GObject):

    __gsignals__ = {
        #'new-item': (GObject.SignalFlags.RUN_FIRST, None, (Grss.FeedChannel, Grss.FeedItem)),
        'items-updated': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    @log
    def __init__(self):
        GObject.GObject.__init__(self)
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        bus.signal_subscribe(
            "org.freedesktop.Tracker1",
            "org.freedesktop.Tracker1.Resources",
            "GraphUpdated",
            "/org/freedesktop/Tracker1/Resources",
            "http://www.tracker-project.org/temp/mfo#FeedMessage",
            Gio.DBusSignalFlags.NONE,
            self.on_graph_updated)
        self.sparql = Trackr.SparqlConnection.get(None)

    @log
    def get_post_sorted_by_date(self, amount):
        results = self.sparql.query("""
        SELECT
          nie:url(?msg)
          nie:title(?msg)
          nco:fullname(nco:creator(?msg))
          nie:contentLastModified(?msg)
          nie:plainTextContent(?msg)
          nmo:isRead(?msg) {
            ?msg a mfo:FeedMessage }
        ORDER BY DESC(nie:contentLastModified(?msg))
        LIMIT %s
        """ % amount)
        ret = []
        for _ in range(amount):
            ret.append([
                results.get_string(0)[0],
                results.get_string(1)[0],
                results.get_string(2)[0],
                0, # FIXME: get date
                results.get_string(4)[0],
                results.get_boolean(5),
            ])
            results.next(None)
        return ret

    @log
    def add_channel(self, url, update_interval=30):
        """Add channel to fetching by tracker

        Args:
            url (str): URL of the channel.
            update_interval (Optional[int]): Update interval in minutes.
                                             Don't use less than 1 minute.
        """
        self.sparql.update("""
        INSERT {
          _:FeedSettings a mfo:FeedSettings ;
                           mfo:updateInterval %i .
          _:Feed a nie:DataObject, mfo:FeedChannel ;
                   mfo:feedSettings _:FeedSettings ;
                   nie:url "%s" }
        """ % (update_interval, url), GLib.PRIORITY_DEFAULT, None)

    @log
    def remove_channel(self, url):
        """Drop channel from fetching by tracker

        Args:
            url (str): URL of the channel.
        """
        self.sparql.update("DELETE { <%s> a mfo:FeedMessage. }" % url)

    @log
    def on_graph_updated(self, connection, sender_name, object_path,
                         interface_name, signal_name, parameters, user_data=None):
        unpacked = parameters.unpack()
        #FIXME: handle deletes -- unpacked[1]
        self._handle_insert_event(unpacked[2])

    @log
    def _handle_insert_event(self, items):
        added_items = 0
        for i in item:
            tmp = EventItem(i)
            # FIXME: handle items
        if added_items > 0:
            self.emit('items-updated')

class EventItem:
    def __init__(self, items):
        """
        Args:
            items (tuple): item tuple
        """
        self.graph_id = items[0]
        self.subject_id = items[1]
        self.pred_id = items[2]
        self.object_id = items[3]
