"""Relationship Navigator Window class.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from xml.sax.saxutils import escape

from schevo.label import label, plural

from schevogtk2.window import Window


class RelationshipWindow(Window):

    gladefile = 'RelationshipNavigator'

    def __init__(self, db, entity):
        super(RelationshipWindow, self).__init__()
        self._db = db
        self._entity = entity
        extent_text = label(entity.sys.extent)
        text = u'%s :: %s' % (extent_text, entity)
        markup = u'<b>%s</b>' % escape(text)
        self.header_label.set_markup(markup)
        self.related_grid.show_hidden_extents = True
        self.related_grid.set_entity(db, entity)

    def on_Hidden__activate(self, action):
        grid = self.related_grid
        grid.show_hidden_extents = not grid.show_hidden_extents

    def on_entity_grid__action_selected(self, widget, action):
        self._on_action_selected(widget, action)

    def on_entity_grid__row_activated(self, widget, entity):
        self.entity_grid.select_view_action()

    def on_related_grid__action_selected(self, widget, action):
        widget = self.entity_grid
        self._on_action_selected(widget, action)

    def on_related_grid__selection_changed(self, widget, related):
        if related is not None:
            extent = related.extent
            text = u'List of related %s:' % plural(extent)
            self.entity_grid_label.set_text(text)
            self.entity_grid.set_related(related)


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2006 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# Saint Louis, MO
# http://orbtech.com/
#
# This toolkit is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This toolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
