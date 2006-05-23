"""Extent Grid widget.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo.label import label, plural

from schevo.gtk import action
from schevo.gtk import grid

import gtk

from kiwi.utils import gsignal, type_register


class ExtentGrid(grid.Grid):

    __gtype_name__ = 'ExtentGrid'

    gsignal('action-selected', object)

    def __init__(self):
        columns = []
        column = grid.Column('_plural', 'Name', data_type=str, sorted=True)
        columns.append(column)
        column = grid.CallableColumn('__len__', 'Qty',
                                     data_type=int, sorted=False)
        columns.append(column)
        super(ExtentGrid, self).__init__(columns)
        self._show_hidden_extents = False
        self._filter = self._model.filter_new()
        self._filter.set_visible_func(self._is_visible)
        self._row_popup_menu = PopupMenu(self)
        self._set_bindings()

    def select_action(self, action):
        self.emit('action-selected', action)

    def select_create_action(self):
        extent = self.get_selected()
        if extent is not None:
            method_name = 'create'
            if method_name in extent.t:
                m_action = action.get_method_action(extent, 't', method_name)
                self.select_action(m_action)

    def set_db(self, db):
        self._db = db
        if db is None:
            extents = []
        else:
            extents = db.extents()
        self.set_rows(extents)

    def _get_show_hidden_extents(self):
        return self._show_hidden_extents

    def _set_show_hidden_extents(self, value):
        self._show_hidden_extents = value
        self._filter.refilter()

    show_hidden_extents = property(fget=_get_show_hidden_extents,
                                   fset=_set_show_hidden_extents)

    def _is_visible(self, model, treeiter):
        extent = model[treeiter][0]
        if extent is None:
            # XXX Find out why this is happening.
            return False
        visible = True
        if extent.hidden and not self._show_hidden_extents:
            visible = False
        return visible

    def _set_bindings(self):
        items = [
            ('Insert', self.select_create_action),
            ]
        self._bindings = dict([(gtk.accelerator_parse(name), func)
                               for name, func in items])

type_register(ExtentGrid)


class PopupMenu(grid.PopupMenu):

    def __init__(self, extent_grid):
        self._extent_grid = extent_grid
        self._extent = None
        super(PopupMenu, self).__init__()

    def get_actions(self):
        extent = self._extent
        items = []
        # Get extent actions.
        actions = action.get_tx_actions(extent)
        if actions:
            items.extend(actions)
        return items

    def popup(self, event, instance):
        self.set_extent(instance)
        super(PopupMenu, self).popup(event, instance)

    def set_extent(self, extent):
        self.clear()
        self._extent = extent
        actions = self.get_actions()
        # Create menu items.
        for action in actions:
            if action is None:
                menuitem = gtk.SeparatorMenuItem()
            else:
                menuitem = gtk.MenuItem(action.label)
                signal_id = menuitem.connect('activate',
                                             self._on_menuitem__activate,
                                             action)
                self._signals.append((menuitem, signal_id))
            menuitem.show()
            self.append(menuitem)

    def _on_menuitem__activate(self, menuitem, action):
        self._extent_grid.select_action(action)


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
