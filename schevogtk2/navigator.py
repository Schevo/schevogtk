"""Database Navigator Window class.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import gtk
from gtk import gdk

import os

from schevo.constant import UNASSIGNED
from schevo import database
from schevogtk2 import form
from schevogtk2 import relationship
## from schevogtk2.dialog import Dialog
from schevo.label import label, plural

from kiwi.environ import require_gazpacho
from kiwi.ui import dialogs
from kiwi.ui.delegates import Delegate

require_gazpacho()

WATCH = gdk.Cursor(gdk.WATCH)


class Window(Delegate):

    gladefile = 'DatabaseNavigator'
    toplevel_name = ''

    def __init__(self, keyactions=None):
        Delegate.__init__(self, delete_handler=self.quit_if_last,
                          keyactions=keyactions,
                          gladefile=self.gladefile,
                          toplevel_name=self.toplevel_name)
        self._db = None
        self._menu_context_id = -1
        self.update_ui()

    def database_close(self):
        """Close an existing database file."""
        if self._db is not None:
            self.set_cursor(WATCH)
            self._db.close()
            self._db = None
            self.entity_grid.set_db(None)
            self.extent_grid.set_db(None)
            self.update_ui()
            self.set_cursor()

##     def database_new(self, filename):
##         """Create a new database file."""

##         # Open the new database.
##         self.database_open(filename)

    def database_open(self, filename):
        """Open a database file."""
        self.database_close()
        self.set_cursor(WATCH)
        self._db = database.open(filename, label=os.path.basename(filename))
        self.entity_grid.set_db(self._db)
        self.extent_grid.set_db(self._db)
        self.update_ui()
        self.set_cursor()

    def database_pack(self):
        """Pack the currently open database file."""
        if self._db is not None:
            self.set_cursor(WATCH)
            self._db.pack()
            self.set_cursor()

    def get_title(self):
        return self.get_toplevel().get_title()

    def on_Close__activate(self, action):
        self.database_close()

    def on_Hidden__activate(self, action):
        grid = self.extent_grid
        grid.show_hidden_extents = not grid.show_hidden_extents

    def on_Open__activate(self, action):
        filename = dialogs.open(parent=self.get_toplevel(),
                                patterns=['*.db', '*.*'],
                                title='Select a database file to open')
        if filename:
            self.database_open(filename)

    def on_Pack__activate(self, action):
        self.database_pack()

    def on_Quit__activate(self, action):
        self.quit_if_last()

    def on_entity_grid__action_selected(self, widget, action):
        self._action_selected(widget, action)

    def on_entity_grid__row_activated(self, widget, entity):
        self.entity_grid.select_view_action()

    def on_extent_grid__action_selected(self, widget, action):
        widget = self.entity_grid
        self._action_selected(widget, action)

    def on_extent_grid__selection_changed(self, widget, extent):
        if extent is not None:
            text = u'List of %s:' % plural(extent)
            self.entity_grid_label.set_text(text)
            self.entity_grid.set_extent(extent)

    def on_uimanager__connect_proxy(self, uimanager, action, widget):
        print 'connect-proxy widget:', widget
        tooltip = action.get_property('tooltip')
        if isinstance(widget, gtk.MenuItem) and tooltip:
            h_id1 = widget.connect(
                'select', self._on_menu_item__select, tooltip)
            h_id2 = widget.connect(
                'deselect', self._on_menu_item__deselect)
            widget.set_data('schevo_app::handler_ids', (h_id1, h_id2))

    def on_uimanager__disconnect_proxy(self, uimanager, action, widget):
        print 'disconnect-proxy widget:', widget
        ids = widget.get_data('schevo_app::handler_ids') or ()
        for handler_id in ids:
            widget.disconnect(handler_id)

    def run_relationship_dialog(self, entity):
        import relationship
        self.set_cursor(WATCH)
        db = self._db
        parent = self.get_toplevel()
        dialog = relationship.Window(db, entity)
        window = dialog.get_toplevel()
        window.set_modal(True)
        window.set_transient_for(parent)
        window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_cursor()
        dialog.run()
        dialog.destroy()

    def run_tx_dialog(self, tx, action):
        self.set_cursor(WATCH)
        db = self._db
        parent = self.get_toplevel()
        dialog = form.get_tx_dialog(parent, db, tx, action)
        self.set_cursor()
        dialog.run()
        tx_result = dialog.tx_result
        dialog.destroy()
        return tx_result

    def run_view_dialog(self, entity, action):
        self.set_cursor(WATCH)
        db = self._db
        parent = self.get_toplevel()
        dialog = form.get_view_dialog(parent, db, entity, action)
        self.set_cursor()
        dialog.run()
        dialog.destroy()

    def set_cursor(self, cursor=None):
        window = self.get_toplevel().window
        # If the app isn't running yet there is no gdk.window.
        if window is not None:
            window.set_cursor(cursor)

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
        if self._db is None:
            self.entity_grid_label.set_text(u'')
            self.Close.set_sensitive(False)
            self.Pack.set_sensitive(False)
        else:
            self.Close.set_sensitive(True)
            self.Pack.set_sensitive(True)

    def _action_selected(self, widget, action):
        if action.type == 'relationship':
            entity = action.instance
            self.run_relationship_dialog(entity)
        elif action.type == 'transaction':
            tx = action.method()
            if action.related is not None:
                # Initialize the related field.
                field_name = action.related.field_name
                if field_name in tx.f:
                    setattr(tx, field_name, action.related.entity)
            tx_result = self.run_tx_dialog(tx, action)
            if tx.sys.executed:
                widget.reflect_changes(tx_result, tx)
        elif action.type == 'view':
            entity = action.instance
            self.run_view_dialog(entity, action)
        # XXX Hack due to a bug where this window doesn't become
        # active when one modal dialog leads to another (including the
        # dialog used by FileChooserButton, or an error message).
        self.get_toplevel().present()

    def _on_menu_item__deselect(self, menuitem):
        self.statusbar.pop(self._menu_context_id)

    def _on_menu_item__select(self, menuitem, tooltip):
        self.statusbar.push(self._menu_context_id, tooltip)


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2006 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# 709 East Jackson Road
# Saint Louis, MO  63119-4241
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
