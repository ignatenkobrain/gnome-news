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

from gi.repository import GLib, GObject, Gio, Tracker as Trackr

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
    def get_post_sorted_by_date(self, amount, unread=False):
        query = """
        SELECT
          nie:url(?msg) AS url
          nie:title(?msg) AS title
          nco:fullname(?creator) AS fullname
          nie:contentCreated(?msg) AS date_created
          nie:plainTextContent(?msg) AS plaintext
          nmo:isRead(?msg) AS is_read
          { ?msg a mfo:FeedMessage """

        if unread:
            query += "; nmo:isRead false"

        query += """; nco:creator ?creator }
        ORDER BY DESC (nie:contentCreated(?msg))
        LIMIT %s
        """ % amount

        logger.debug(query)
        results = self.sparql.query(query)
        ret = []
        while (results.next(None)):
            ret.append(self.parse_sparql(results))
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
        self.sparql.update("DELETE { <%s> a mfo:FeedMessage. }" % url,
                           GLib.PRIORITY_DEFAULT, None)

    @log
    def get_posts_for_channel(self, urn, amount, unread=False):
        """Get posts for channel id

        Args:
            urn (str): urn:uuid:... of the channel.
            amount (int): number of items to fetch.
            unread (Optional[bool]): return only unread items if True.
        """
        query = """
        SELECT
          nie:url(?msg) AS url
          nie:title(?msg) AS title
          nco:fullname(?creator) AS fullname
          nie:contentCreated(?msg) AS date_created
          nie:plainTextContent(?msg) AS plaintext
          nmo:isRead(?msg) AS is_read
          { ?msg a mfo:FeedMessage;
                 nmo:communicationChannel <%s> """

        if unread:
            query += "; nmo:isRead false"

        query += """; nco:creator ?creator }
        ORDER BY DESC nie:contentLastModified(?msg)
        LIMIT %s
        """ % (urn, amount)

        logger.debug(query)
        results = self.sparql.query(query)
        ret = []
        while (results.next(None)):
            ret.append(self.parse_sparql(results))
        return ret

    def get_channels(self):
        """Returns list of channels"""
        query = """
        SELECT
          nie:url(?chan) AS url
          nie:title(?chan) AS title
          nie:description(?chan) AS description
          ?chan AS channel
          { ?chan a mfo:FeedChannel }
        ORDER BY nie:title(?chan)
        """

        logger.debug(query)
        results = self.sparql.query(query)
        ret = []
        while (results.next(None)):
            ret.append(self.parse_sparql(results))
        return ret

    def get_text_matches(self, text, amount, channel=None):
        """Do text search lookup

        Args:
            text (str): text to search for.
            channel (str): urn:uuid:... of the channel.
            amount (int): number of items to fetch.
        """
        query = """
        SELECT
          nie:url(?msg) AS url
          nie:title(?msg) AS title
          nco:fullname(?creator) AS fullname
          nie:contentCreated(?msg) AS date_created
          nie:plainTextContent(?msg) AS plaintext
          nmo:isRead(?msg) AS is_read
          { ?msg a mfo:FeedMessage; """

        if channel:
            query += """nmo:communicationChannel <%s>;""" % channel

        query += """
                 fts:match "%s";
                 nco:creator ?creator
          }
        ORDER BY fts:rank(?msg)
        LIMIT %d
        """ % (text, amount)

        logger.debug(query)
        results = self.sparql.query(query)
        ret = []
        while (results.next(None)):
            ret.append(self.parse_sparql(results))
        return ret

    @log
    def on_graph_updated(self, connection, sender_name, object_path,
                         interface_name, signal_name, parameters, user_data=None):
        unpacked = parameters.unpack()
        #FIXME: handle deletes -- unpacked[1]
        self._handle_insert_event(unpacked[2])

    @log
    def _handle_insert_event(self, items):
        added_items = 0
        for i in items:
            tmp = EventItem(i)
            # FIXME: handle items
        if added_items > 0:
            self.emit('items-updated')

    @staticmethod
    @log
    def parse_sparql(sparql_ret):
        ret = {}
        n_columns = sparql_ret.get_n_columns()
        for column in range(n_columns):
            t = sparql_ret.get_value_type(column)
            name = sparql_ret.get_variable_name(column)
            if any([t == Trackr.SparqlValueType.URI,
                    t == Trackr.SparqlValueType.STRING]):
                value = sparql_ret.get_string(column)[0]
            elif t == Trackr.SparqlValueType.DATETIME:
                # Tracker returns ISO 8601 format
                tv = GLib.TimeVal.from_iso8601(sparql_ret.get_string(column)[0])
                value = GLib.DateTime.new_from_timeval_local(tv[1])
            elif t == Trackr.SparqlValueType.BOOLEAN:
                value = sparql_ret.get_boolean(column)
            else:
                value = None
                logger.error("We should not get this type from sparql. name: %s, type: %s", name, t)
            ret[name] = value
        return ret

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
