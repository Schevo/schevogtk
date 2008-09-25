"""Related Grid widget.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo.label import label, plural

from schevogtk2 import action
from schevogtk2 import grid
from schevogtk2 import icon
from schevogtk2.utils import gsignal, type_register

import gtk


class Related(object):

    def __init__(self, entity, extent, field_name):
        self.entity = entity
        self.extent = extent
        self.plural = plural(extent)
        self.field_name = field_name
        self.field_label = label(extent.field_spec.field_map()[field_name])

    def __cmp__(self, other):
        if other.__class__ is self.__class__:
            return cmp((self.entity, self.plural, self.field_label),
                       (other.entity, other.plural, other.field_label))
        else:
            return cmp(hash(self), hash(other))

    def __len__(self):
        return self.entity.s.count(self.extent.name, self.field_name)

    def __repr__(self):
        return '%s %s %s' % (self.entity, self.extent, self.field_name)


class RelatedExtentColumn(grid.Column):

    _has_icon = True

    def cell_icon(self, column, cell, model, row):
        extent = model[row][0].extent
        pixbuf = icon.small_pixbuf(self, extent)
        cell.set_property('pixbuf', pixbuf)


class RelatedGrid(grid.Grid):

    __gtype_name__ = 'RelatedGrid'

    gsignal('action-selected', object)

    def __init__(self):
        grid.Grid.__init__(self)
        self._show_hidden_extents = False
        self._filter = self._model.filter_new()
        self._filter.set_visible_func(self._is_visible)
        self._sorter = gtk.TreeModelSort(self._filter)
        self._row_popup_menu = PopupMenu(self)
        self._set_bindings()
        columns = []
        column = RelatedExtentColumn('plural', 'Name', str)
        columns.append(column)
        column = grid.Column('field_label', 'Field', str)
        columns.append(column)
        column = grid.Column('__len__', 'Qty', int, call=True)
        columns.append(column)
        self.set_columns(columns)

    def select_action(self, action):
        self.emit('action-selected', action)

    def select_create_action(self):
        related = self.get_selected()
        extent = related.extent
        if extent is not None:
            method_name = 'create'
            if method_name in extent.t:
                m_action = action.get_method_action(extent, 't', method_name,
                                                    related)
                self.select_action(m_action)

    def set_entity(self, db, entity):
        self._db = db
        relateds = []
        for extent_name, field_name in entity.s.extent.relationships:
            extent = db.extent(extent_name)
            related = Related(entity, extent, field_name)
            relateds.append(related)
        self.set_rows(relateds)

    def _get_show_hidden_extents(self):
        return self._show_hidden_extents

    def _set_show_hidden_extents(self, value):
        self._show_hidden_extents = value
        self._filter.refilter()

    show_hidden_extents = property(fget=_get_show_hidden_extents,
                                   fset=_set_show_hidden_extents)

    def _is_visible(self, model, row):
        related = model[row][0]
        if related is None:
            # XXX Find out why this is happening.
            return False
        extent = related.extent
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

type_register(RelatedGrid)


class PopupMenu(grid.PopupMenu):

    def __init__(self, related_grid):
        self._related_grid = related_grid
        self._extent = None
        grid.PopupMenu.__init__(self)

    def get_actions(self):
        extent = self._extent
        related = self._related_grid.get_selected()
        items = []
        # Get extent actions.
        actions = action.get_tx_actions(extent, related)
        if actions:
            items.extend(actions)
            items.append(None)
        return items

    def popup(self, event, instance):
        extent = instance.extent
        self.clear()
        self.set_extent(extent)
        grid.PopupMenu.popup(self, event, extent)

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
        self._related_grid.select_action(action)


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2007 Orbtech, L.L.C.
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
