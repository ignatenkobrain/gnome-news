# Demo RSS client using tracker as backend
# Copyright(C) 2009 Nokia <ivan.frade@nokia.com>
# Copyright(C) 2015 Vadim Rutkovsky <vrutkovs@redhat.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or(at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

import dbus
from datetime import datetime
from gi.repository import GObject, Tracker

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


TRACKER = 'org.freedesktop.Tracker1'
TRACKER_OBJ = '/org/freedesktop/Tracker1/Resources'

FALSE = "false"
TRUE = "true"

QUERY_FIRST_ENTRIES = """
    SELECT ?entry ?title ?date ?author ?text ?isRead WHERE {
      ?entry a mfo:FeedMessage ;
         nie:title ?title ;
         nie:contentLastModified ?date ;
         nmo:from ?author ;
         nie:plainTextContent ?text .
    OPTIONAL {
       ?entry nmo:isRead ?isRead.
    }
    } ORDER BY DESC(?date) LIMIT %s
    """

SET_URI_AS_READED = """
    DELETE {<%s> nmo:isRead "%s".}
    INSERT {<%s> nmo:isRead "%s".}
    """

QUERY_ALL_SUBSCRIBED_FEEDS = """
    SELECT ?feeduri ?title COUNT(?entries) AS e WHERE {
       ?feeduri a mfo:FeedChannel ;
                nie:title ?title.
       ?entries a mfo:FeedMessage ;
                nmo:communicationChannel ?feeduri.
    } GROUP BY ?feeduri
"""

QUERY_FOR_URI = """
    SELECT ?title ?date ?author ?isRead ?channel WHERE {
      <%s> a mfo:FeedMessage ;
             nie:title ?title ;
             nmo:from ?author ;
             nie:contentLastModified ?date ;
             nmo:communicationChannel ?channel .
      OPTIONAL {
      <%s> nmo:isRead ?isRead.
      }
    }
"""

INSERT_QUERY = """
    INSERT OR REPLACE {
        <%s> a mfo:FeedMessage ;
         nie:contentLastModified "%s" ;
         nmo:communicationChannel <%s>;
         nmo:from "%s" ;
         nie:plainTextContent "%s" ;
         nie:title "%s".
    }
"""

QUERY_FOR_TEXT = """
    SELECT ?text WHERE {
    <%s> nie:plainTextContent ?text .
    }
"""


class TrackerRSS(GObject.GObject):
    @log
    def __init__(self):
        GObject.GObject.__init__(self)
        bus = dbus.SessionBus()
        self.tracker = bus.get_object(TRACKER, TRACKER_OBJ)
        self.iface = dbus.Interface(self.tracker,
                                    "org.freedesktop.Tracker1.Resources")

    @log
    def get_post_sorted_by_date(self, amount):
        results = self.iface.SparqlQuery(QUERY_FIRST_ENTRIES % (amount))
        return results

    @log
    def set_is_read(self, uri, value):
        if(value):
            dbus_value = TRUE
            anti_value = FALSE
        else:
            dbus_value = FALSE
            anti_value = TRUE

        self.iface.SparqlUpdate(SET_URI_AS_READED % (uri, anti_value, uri, dbus_value))

    @log
    def get_all_subscribed_feeds(self):
        """ Returns [(uri, feed channel name, entries, visible)]
        """
        results = self.iface.SparqlQuery(QUERY_ALL_SUBSCRIBED_FEEDS)
        return results

    @log
    def get_info_for_entry(self, uri):
        """  Returns(?title ?date ?isRead)
        """
        details = self.iface.SparqlQuery(QUERY_FOR_URI % (uri, uri))
        if len(details) != 1:
            return None

        info = details[0]
        if(info[2] == TRUE):
            return(info[0], info[1], True)
        else:
            return(info[0], info[1], False)

    @log
    def get_text_for_uri(self, uri):
        text = self.iface.SparqlQuery(QUERY_FOR_TEXT % (uri))
        if(text[0]):
            text = text[0][0].replace("\\n", "\n")
        else:
            text = ""
        return text

    @log
    def new_feed_item_signal(self, fetcher, feed, item):
        try:
            uri = item.get_source()
            # if self.get_info_for_entry(uri) is not None:
            #     logger.info("Item %s is already added" % uri)
            #     return

            source_uri = feed.get_source()
            timestamp = item.get_publish_time()
            author = item.get_author()
            date = datetime.fromtimestamp(timestamp).isoformat()
            title = item.get_title()
            text = item.get_description()
            escaped_text = Tracker.sparql_escape_string(text)

            query = INSERT_QUERY % (uri, date, source_uri, author, escaped_text, title)
            logger.info("New feed: \n%s" % query)
            self.iface.SparqlUpdate(query)
        except Exception as e:
            logger.warn(str(e))
