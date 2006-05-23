"""Entity Grid widget.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import schevo.field
from schevo.label import label, plural

from schevo.gtk import action
from schevo.gtk import grid

import gtk

from kiwi.utils import gsignal, type_register


class EntityGrid(grid.Grid):

    __gtype_name__ = 'EntityGrid'

    gsignal('action-selected', object)

    def __init__(self):
        super(EntityGrid, self).__init__()
        self._autosize = False
        self._extent = None
        self._related = None
        self._oids = {}
        self._row_popup_menu = PopupMenu(self)
        self._set_bindings()

    def add_row(self, oid):
        instance = self._extent[oid]
        inst_id = id(instance)
        self._oids[oid] = inst_id
        self._iters[inst_id] = self._model.append((instance,))

    def remove_row(self, oid):
        model = self._model
        inst_id = self._oids.pop(oid)
        # Get the current position.
        row_iter = self._iters[inst_id]
        pos = model[row_iter].path[0]
        # Remove the instance.
        self._remove(inst_id)
        # Select the next logical row, if any remain.
        end = len(model) - 1
        if pos > end:
            pos = end
        if pos > -1:
            other = model[pos][0]
            self.select(other)

    def select_row(self, oid):
        inst_id = self._oids[oid]
        row_iter = self._iters[inst_id]
        self._select_and_focus_row(row_iter)

    def reflect_changes(self, result, tx):
        summary = tx.sys.summarize()
        oids = summary.deletes.get(self._extent.name, [])
        for oid in oids:
            self.remove_row(oid)
        oids = summary.creates.get(self._extent.name, [])
        for oid in oids:
            self.add_row(oid)
        if result is not None:
            self.select_row(result.sys.oid)

    def select_action(self, action):
        self.emit('action-selected', action)

    def select_create_action(self):
        extent = self._extent
        if extent is not None:
            method_name = 'create'
            if method_name in extent.t:
                m_action = action.get_method_action(extent, 't', method_name,
                                                    self._related)
                self.select_action(m_action)

    def select_delete_action(self):
        entity = self.get_selected()
        if entity is not None:
            method_name = 'delete'
            if method_name in entity.t:
                m_action = action.get_method_action(entity, 't', method_name)
                self.select_action(m_action)

    def select_update_action(self):
        entity = self.get_selected()
        if entity is not None:
            method_name = 'update'
            if method_name in entity.t:
                m_action = action.get_method_action(entity, 't', method_name)
                self.select_action(m_action)

    def select_view_action(self):
        entity = self.get_selected()
        if entity is not None:
            v_action = action.get_view_action(entity, include_expensive=False)
            self.select_action(v_action)

    def set_db(self, db):
        self._db = db
        if db is None:
            self.set_extent(None)

    def set_extent(self, extent):
        if extent == self._extent:
            return
        self._extent = extent
        self._row_popup_menu.set_extent(extent)
        self.set_rows([])
        self.set_columns([])
        if extent is not None:
            columns = self._get_columns_for_extent(extent)
            results = extent.find()
            self.set_columns(columns)
            self.set_rows(results)

    def set_related(self, related):
        if related == self._related:
            return
        self._related = related
        extent = related.extent
        self._extent = extent
        self._row_popup_menu.set_extent(extent)
        self.set_rows([])
        self.set_columns([])
        if extent is not None:
            columns = self._get_columns_for_extent(extent)
            results = related.entity.sys.links(extent.name, related.field_name)
            self.set_columns(columns)
            self.set_rows(results)

    def set_rows(self, instances):
        oids = self._oids
        oids.clear()
        for instance in instances:
            inst_id = id(instance)
            oids[instance.sys.oid] = inst_id
        super(EntityGrid, self).set_rows(instances)

    def _get_columns_for_extent(self, extent):
        columns = []
        column = grid.Column('_oid', 'OID', data_type=int, sorted=True)
        columns.append(column)
##         column = grid.Column('sys.rev', 'Rev', data_type=int)
##         columns.append(column)
        for field_name, FieldClass in extent.field_spec.iteritems():
            data_type = str
##             # XXX Don't like the look of a boolean column.
##             if issubclass(FieldClass, schevo.field.Boolean):
##                 data_type = bool
            if issubclass(FieldClass, schevo.field.Float):
                data_type = float
            if issubclass(FieldClass, schevo.field.Integer):
                data_type = int
            if not FieldClass.expensive and not FieldClass.hidden:
                title = label(FieldClass)
                column = grid.Column(field_name, title, data_type=data_type)
                columns.append(column)
        return columns

    def _set_bindings(self):
        items = [
            ('Insert', self.select_create_action),
            ('<Control>Return', self.select_update_action),
            ('Delete', self.select_delete_action),
            ]
        self._bindings = dict([(gtk.accelerator_parse(name), func)
                               for name, func in items])

type_register(EntityGrid)


class PopupMenu(grid.PopupMenu):

    def __init__(self, entity_grid):
        self._entity_grid = entity_grid
        self._extent = None
        self._entity = None
        super(PopupMenu, self).__init__()

    def get_actions(self):
        extent = self._extent
        entity = self._entity
        items = []
        # Extent tx actions.
        actions = action.get_tx_actions(extent, self._entity_grid._related)
        if actions:
            if items:
                items.append(None)
            items.extend(actions)
        # Entity view actions.
        actions = action.get_view_actions(entity)
        if actions:
            if items:
                items.append(None)
            items.extend(actions)
        # Entity relationship actions.
        actions = action.get_relationship_actions(entity)
        if actions:
            if items:
                items.append(None)
            items.extend(actions)
        # Entity tx actions.
        actions = action.get_tx_actions(entity)
        if actions:
            if items:
                items.append(None)
            items.extend(actions)
        return items

    def popup(self, event, instance):
        self.set_entity(instance)
        super(PopupMenu, self).popup(event, instance)

    def set_entity(self, entity):
        self.clear()
        self._entity = entity
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

    def set_extent(self, extent):
        self.clear()
        self._extent = extent

    def _on_menuitem__activate(self, menuitem, action):
        self._entity_grid.select_action(action)


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
