"""Relationship Navigator Window class."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from xml.sax.saxutils import escape

from schevo.label import label, plural

from schevogtk2.window import Window


class RelationshipWindow(Window):

    gladefile = 'RelationshipNavigator'

    def __init__(self, db, entity):
        Window.__init__(self)
        self._db = db
        self._entity = entity
        extent_text = label(entity.s.extent)
        text = u'%s :: %s' % (extent_text, entity)
        markup = u'<b>%s</b>' % escape(text)
        self.header_label.set_markup(markup)
        self.related_grid.show_hidden_extents = True
        self.related_grid.set_entity(db, entity)
        self.entity_grid.set_db(db)

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
