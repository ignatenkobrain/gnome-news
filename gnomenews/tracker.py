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
        # 'new-item': (GObject.SignalFlags.RUN_FIRST, None, (Grss.FeedChannel, Grss.FeedItem)),
        'items-updated': (GObject.SignalFlags.RUN_LAST, None, ()),
        'feeds-updated': (GObject.SignalFlags.RUN_LAST, None, ()),
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
    def get_post_sorted_by_date(self, amount, unread=False, starred=False):
        query = """
        SELECT
          nie:url(?msg) AS url
          nie:title(?msg) AS title
          nco:fullname(?creator) AS fullname
          nie:url(?website) AS author_homepage
          nco:emailAddress(?email) AS author_email
          nie:contentCreated(?msg) AS date
          nmo:htmlMessageContent(?msg) AS content
          nmo:isRead(?msg) AS is_read
        WHERE
          { ?msg a mfo:FeedMessage """

        if unread:
            query += "; nmo:isRead false"

        if starred:
            query += "; nao:hasTag nao:predefined-tag-favorite "

        query += """; nco:creator ?creator.
            OPTIONAL {?creator nco:hasEmailAddress ?email } .
            OPTIONAL {?creator nco:websiteUrl ?website }
          }
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
    def get_info_for_entry(self, url):
        query = """
        SELECT
          nie:title(?msg) AS title
          nco:fullname(?creator) AS fullname
          nie:url(?website) AS author_homepage
          nco:emailAddress(?email) AS author_email
        WHERE
          { ?msg a mfo:FeedMessage ;
                 nco:creator ?creator ;
                 nie:url <%s> .
            OPTIONAL { ?creator nco:hasEmailAddress ?email } .
            OPTIONAL { ?creator nco:websiteUrl ?website }
          }""" % url

        logger.debug(query)
        results = self.sparql.query(query)
        ret = []
        while (results.next(None)):
            ret.append(self.parse_sparql(results))
        if len(ret) != 1:
            raise Exception("More than one result returned by feed with url %s" % url)
        return ret[0]

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
    def mark_post_as_read(self, caller, url, data=None):
        """Marks given post as read

        Args:
            url (str): URL of the post.
            data (Optional): user data.
        """

        query = """
        DELETE
          { ?msg nmo:isRead ?any }
        WHERE
          { ?msg nie:url "%s";
                 nmo:isRead ?any }
        INSERT
          { ?msg nmo:isRead true }
        WHERE
          { ?msg nie:url "%s" }
        """ % (url, url)

        logger.debug(query)
        self.sparql.update(query, GLib.PRIORITY_DEFAULT, None)

    @log
    def remove_channel(self, url):
        """Drop channel from fetching by tracker

        Args:
            url (str): URL of the channel.
        """
        query = """
        DELETE
          { ?mess a mfo:FeedMessage }
        WHERE
          { ?chan nie:url "%s" }
        DELETE
          { ?chan a mfo:FeedChannel }
        WHERE
          { ?chan nie:url "%s" }
        """ % (url, url)
        logger.debug(query)
        self.sparql.update(query, GLib.PRIORITY_DEFAULT, None)

    @log
    def get_posts_for_channel(self, url, amount):
        """Get posts for channel id

        Args:
            url (str): URL of the channel.
            amount (int): number of items to fetch.
            unread (Optional[bool]): return only unread items if True.
        """
        query = """
        SELECT
          nie:url(?msg) AS url
          nie:title(?msg) AS title
          nco:fullname(?creator) AS fullname
          nie:url(?website) AS author_homepage
          nco:emailAddress(?email) AS author_email
          nie:contentCreated(?msg) AS date
          nmo:htmlMessageContent(?msg) AS content
          nmo:isRead(?msg) AS is_read
          { ?msg a mfo:FeedMessage;
                 nmo:communicationChannel ?chan;
                 nco:creator ?creator
                   { ?chan nie:url "%s" }.
            OPTIONAL { ?creator nco:hasEmailAddress ?email } .
            OPTIONAL { ?creator nco:websiteUrl ?website }
          }
        ORDER BY DESC (nie:contentCreated(?msg))
        LIMIT %s
        """ % (url, amount)

        logger.debug(query)
        results = self.sparql.query(query)
        ret = []
        while (results.next(None)):
            ret.append(self.parse_sparql(results))
        return ret

    @log
    def get_channels(self, url=None):
        """Returns list of channels

        Args:
            url (Optional[str]): URL of the channel

        Returns:
            list of all channels of list limited to one channel if url is
            not None
        """
        query = """
        SELECT
          nie:url(?chan) AS url
          nie:title(?chan) AS title
          { ?chan a mfo:FeedChannel"""

        if url is not None:
            query += """; nie:url "%s" """ % url
        query += """
          }
        ORDER BY nie:title(?chan)
        """

        results = self.sparql.query(query)
        ret = []
        while (results.next(None)):
            ret.append(self.parse_sparql(results))
        return ret

    @log
    def get_text_matches(self, text, amount, channel=None):
        """Do text search lookup

        Args:
            text (str): text to search for.
            channel (str): URL of the channel.
            amount (int): number of items to fetch.
        """
        query = """
        SELECT
          nie:url(?msg) AS url
          nie:title(?msg) AS title
          nco:fullname(?creator) AS fullname
          nie:url(?website) AS author_homepage
          nco:emailAddress(?email) AS author_email
          nie:contentCreated(?msg) AS date_created
          nmo:htmlMessageContent(?msg) AS content
          nmo:isRead(?msg) AS is_read
          { ?msg a mfo:FeedMessage; """

        if channel:
            query += """nmo:communicationChannel ?chan;"""

        query += """
                 fts:match "%s";
                 nco:creator ?creator
                 { ?chan nie:url "%s" }.
            OPTIONAL { ?creator nco:hasEmailAddress ?email } .
            OPTIONAL { ?creator nco:websiteUrl ?website }
          }
        ORDER BY fts:rank(?msg)
        LIMIT %d
        """ % (text, channel, amount)

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
        # FIXME: handle deletes -- unpacked[1]
        GLib.idle_add(self._handle_insert_event, unpacked[2])

    @log
    def _handle_insert_event(self, items):
        self.emit('items-updated')
        self.emit('feeds-updated')

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
            elif t == Trackr.SparqlValueType.INTEGER:
                value = sparql_ret.get_integer(column)
            elif t == Trackr.SparqlValueType.DOUBLE:
                value = sparql_ret.get_double(column)
            else:
                try:
                    value = sparql_ret.get_string(column)[0]
                except Exception:
                    value = None
                    logger.error("Can't get string value from sparql. name: %s, type: %s", name, t)
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
