"""Database Navigator Window class."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from __future__ import with_statement

import sys
from schevo.lib import optimize

import gtk

import os

from schevo import database
from schevo.label import label, plural

from schevogtk2.cursor import TemporaryCursor
from schevogtk2 import icon
from schevogtk2.window import Window


class NavigatorWindow(Window):

    gladefile = 'DatabaseNavigator'

    if os.name == 'nt':
        file_ext_filter = 'Schevo Database Files\0*.db;*.schevo\0'
        file_custom_filter = 'All Files\0*.*\0'
        file_open_title = 'Open Schevo Database File'

    def __init__(self):
        Window.__init__(self)
        self.update_ui()

##     def database_new(self, filename):
##         """Create a new database file."""

##         # Open the new database.
##         self.database_open(filename)

    def database_new(self, filename):
        """Create a new database file."""
        pass

    def on_Hidden__activate(self, action):
        grid = self.extent_grid
        grid.show_hidden_extents = not grid.show_hidden_extents

    def on_Pack__activate(self, action):
        self.database_pack()

    def on_entity_grid__action_selected(self, widget, action):
        self._on_action_selected(widget, action)

    def on_entity_grid__row_activated(self, widget, entity):
        self._on_grid__row_activated(widget, entity)

    def on_extent_grid__action_selected(self, widget, action):
        widget = self.entity_grid
        self._on_action_selected(widget, action)

    def on_extent_grid__selection_changed(self, widget, extent):
        if extent is not None:
            with TemporaryCursor(self):
                self._db.backend.rollback()
                icon_set = icon.iconset(widget, extent)
                size = gtk.ICON_SIZE_LARGE_TOOLBAR
                self.entity_grid_image.set_from_icon_set(icon_set, size)
                text = u'List of %s:' % plural(extent)
                self.entity_grid_label.set_text(text)
                self.entity_grid.set_extent(extent)

    def update_title(self):
        """Add or remove the database label from the end of the title."""
        separator = u' :: '
        text = self.get_title()
        # Get only the text in front of the separator.
        text = text.split(separator, 1)[0]
        if self._db:
            text = text + separator + label(self._db)
        self.set_title(text)

    def update_ui(self):
        """Update the interface to reflect the state of the database."""
        self.update_title()
        self.entity_grid.set_db(self._db)
        self.extent_grid.set_db(self._db)
        if self._db is None:
            size = gtk.ICON_SIZE_LARGE_TOOLBAR
            self.entity_grid_image.set_from_stock(gtk.STOCK_INFO, size)
            self.entity_grid_label.set_text(u'Open a database file.')
            self.Close.set_sensitive(False)
            self.Pack.set_sensitive(False)
        else:
            self.entity_grid_label.set_text(u'Select an extent to view.')
            self.Close.set_sensitive(True)
            self.Pack.set_sensitive(True)


optimize.bind_all(sys.modules[__name__])  # Last line of module.
