"""Relationship Navigator Window class.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import gtk
from gtk import gdk

from schevogtk2 import form

from schevo.label import label, plural

from kiwi.environ import require_gazpacho
from kiwi.ui.delegates import Delegate

require_gazpacho()

WATCH = gdk.Cursor(gdk.WATCH)


class Window(Delegate):

    gladefile = 'RelationshipNavigator'
    toplevel_name = ''

    def __init__(self, db, entity, keyactions=None):
        Delegate.__init__(self,
                          keyactions=keyactions,
                          gladefile=self.gladefile,
                          toplevel_name=self.toplevel_name)
        self._db = db
        self._entity = entity
        extent_text = label(entity.sys.extent)
        text = u'%s :: %s' % (extent_text, entity)
        self.header_label.set_label(text)
        self.header_label.set_bold(True)
        self.get_toplevel().connect('hide', self.quit)
        self.related_grid.show_hidden_extents = True
        self.related_grid.set_entity(db, entity)

    def destroy(self, *args):
        self.get_toplevel().destroy()

    def get_title(self):
        return self.get_toplevel().get_title()

    def on_Hidden__activate(self, action):
        grid = self.related_grid
        grid.show_hidden_extents = not grid.show_hidden_extents

    def on_entity_grid__action_selected(self, widget, action):
        self._action_selected(widget, action)

    def on_entity_grid__row_activated(self, widget, entity):
        self.entity_grid.select_view_action()

    def on_related_grid__action_selected(self, widget, action):
        widget = self.entity_grid
        self._action_selected(widget, action)

    def on_related_grid__selection_changed(self, widget, related):
        if related is not None:
            extent = related.extent
            text = u'List of related %s:' % plural(extent)
            self.entity_grid_label.set_text(text)
            self.entity_grid.set_related(related)

    def quit(self, *args):
        gtk.main_quit()

    def run(self):
        self.show()
        gtk.main()

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
