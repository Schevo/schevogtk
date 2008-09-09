"""Entity Grid widget.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo import base
from schevo import field
from schevo.label import label, plural
from schevo.constant import UNASSIGNED
from schevo.error import EntityDoesNotExist

from schevogtk2.action import (
    get_method_action, get_relationship_actions,
    get_tx_actions, get_view_action, get_view_actions)
from schevogtk2 import grid
from schevogtk2 import icon
from schevogtk2.utils import gsignal, type_register

import gtk

from schevogtk2.grid import OBJECT_COLUMN


class FieldColumn(grid.Column):

    def cell_data_getattr(self, instance, attribute):
        return getattr(instance.f, attribute)


class EntityColumn(grid.Column):

    _has_icon = True

    def cell_icon(self, column, cell, model, row_iter):
        grid.Column.cell_icon(self, column, cell, model, row_iter)
        instance = model[row_iter][OBJECT_COLUMN]
        try:
            entity = getattr(instance, self.attribute)
        except EntityDoesNotExist:
            entity = UNASSIGNED
        if entity is UNASSIGNED:
            cell.set_property('stock_id', gtk.STOCK_NO)
            cell.set_property('stock_size', gtk.ICON_SIZE_SMALL_TOOLBAR)
            cell.set_property('visible', False)
        else:
            extent = entity.sys.extent
            pixbuf = icon.small_pixbuf(self, extent)
            cell.set_property('pixbuf', pixbuf)
            cell.set_property('visible', True)


class EntityGrid(grid.Grid):

    __gtype_name__ = 'EntityGrid'

    gsignal('action-selected', object)

    # Set to False if 'Relationships' option should not show up in
    # popup menus.
    show_relationships_in_menu = True

    def __init__(self, model_info=None):
        grid.Grid.__init__(self)
        self._hidden = []  # List of fieldnames of columns to hide.
        self._row_popup_menu = PopupMenu(self)
        self._set_bindings()
        self.reset()
        if model_info is not None:
            (self._model,
             self._sorter,
             self._extent,
             self._query,
             self._related,
             self._hidden,
             columns,
             ) = model_info
            if self._sorter is not None:
                self._view.set_model(self._sorter)
            else:
                self._view.set_model(self._model)
            self.set_columns(columns)

    def add_row(self, oid):
        instance = self._extent[oid]
        row_iter = grid.Grid.add_row(self, instance)
        self._row_map[oid] = row_iter

    def columns_autosize_if_needed(self):
        # Resize columns if 25 or fewer rows.
        model = self._model
        if len(model) <= 25:
            self._view.columns_autosize()

    def identify(self, instance):
        return instance._oid

    def model_info(self):
        return (
            self._model,
            self._sorter,
            self._extent,
            self._query,
            self._related,
            self._hidden[:],
            self._columns[:],
            )

    def reflect_changes(self, result, tx):
        if self._extent is not None:
            summary = tx.sys.summarize()
            for oid in summary.deletes.get(self._extent.name, []):
                self.remove_row(oid)
            for oid in summary.creates.get(self._extent.name, []):
                self.add_row(oid)
            if isinstance(result, self._extent._EntityClass):
                self.select_row(result.sys.oid)
            self.columns_autosize_if_needed()

    def refresh(self):
        extent = self._extent
        query = self._query
        related = self._related
        oids = []
        if query is not None:
            if len(self._columns) == 0:
                # We do not yet know the columns, which means that we
                # do not yet have any query results, so we can reset the
                # grid as if we have a new query.
                self.set_query(None)
                self.set_query(query)
            else:
                # Get current selection identity so we can reselect it.
                selected = self.get_selected()
                if selected is None:
                    identity = None
                elif isinstance(selected, list):
                    identity = [self.identify(entity) for entity in selected]
                else:
                    identity = self.identify(selected)
                # Refresh query.
                results = query()
                self.set_rows([])
                self.set_rows(results)
                # Reselect the identity.
                if identity is None:
                    pass
                elif isinstance(identity, list):
                    self.select_rows(identity)
                else:
                    self.select_row(identity)
        elif related is not None:
            if related.entity.sys.exists:
                if extent is not None:
                    results = related.entity.sys.links(extent.name,
                                                       related.field_name)
                    oids = [entity._oid for entity in results]
                    self.refresh_add_delete(oids)
            else:
                self.set_related(None)
        elif extent is not None:
            oids = extent.find_oids()
            self.refresh_add_delete(oids)
        self.refilter()
        self.columns_autosize_if_needed()

    def refresh_add_delete(self, oids):
        row_map = self._row_map
        # Delete entities that no longer exist.
        for oid in row_map.keys():
            if oid not in oids:
                self.remove_row(oid)
        # Add new entities.
        for oid in oids:
            if oid not in row_map:
                self.add_row(oid)

    def remove_row(self, oid):
        if oid not in self._row_map:
            return
        model = self._model
        row_iter = self._row_map.pop(oid)
        # Get the current position.
        pos = model[row_iter].path[0]
        # Remove the instance.
        model.remove(row_iter)
        # Select the next logical row, if any remain.
        end = len(model) - 1
        if pos > end:
            pos = end
        if pos > -1:
            other = model[pos][OBJECT_COLUMN]
            self.select(other)

    def reset(self):
        self._extent = None
        self._query = None
        self._related = None
        if self._row_popup_menu is not None:
            self._row_popup_menu.set_extent(None)
        self.set_rows([])
        self.set_columns([])

    def select_action(self, action):
        self.emit('action-selected', action)

    def select_create_action(self):
        extent = self._extent
        if extent is not None:
            method_name = 'create'
            if method_name in extent.t:
                m_action = get_method_action(extent, 't', method_name,
                                             self._related)
                self.select_action(m_action)

    def select_delete_action(self):
        entity = self.get_selected()
        if entity is not None:
            method_name = 'delete'
            if method_name in entity.t:
                m_action = get_method_action(entity, 't', method_name)
                self.select_action(m_action)

    def select_update_action(self):
        entity = self.get_selected()
        if entity is not None:
            method_name = 'update'
            if method_name in entity.t:
                m_action = get_method_action(entity, 't', method_name)
                self.select_action(m_action)

    def select_view_action(self):
        entity = self.get_selected()
        if (entity is not None
            and (entity._hidden_views is None
                 or 'default' not in entity._hidden_views
                 )
            ):
            v_action = get_view_action(entity, include_expensive=False)
            self.select_action(v_action)

    def select_row(self, oid):
        row_iter = self._row_map.get(oid, None)
        if row_iter is not None:
            self.select_and_focus_row(row_iter)

    def select_rows(self, oids):
        selection = self._view.get_selection()
        for oid in oids:
            row_iter = self._row_map.get(oid, None)
            if row_iter is not None:
                selection.select_iter(row_iter)

    def set_all_x(self, name, value):
        """Set x.name to value for all entities."""
        for item in self._model:
            entity = item[OBJECT_COLUMN]
            setattr(entity.x, name, value)

    def set_db(self, db):
        self._db = db
        if db is None:
            self.reset()

    def set_extent(self, extent):
        if extent == self._extent:
            return
        self.reset()
        if extent is not None:
            self._extent = extent
            self._row_popup_menu.set_extent(extent)
            columns = self._get_columns_for_field_spec(extent.field_spec)
            self.set_columns(columns)
            self.set_rows(extent)

    def set_query(self, query):
        if query == self._query:
            return
        self.reset()
        if query is not None:
            self._query = query
            # For now, assume the results are homogenous and take the
            # field_spec of the first result.
            field_spec = None
            results = query()
            if not isinstance(results, list):
                # Work around the fact that queries may return
                # iterators by returning non-lists into lists.
                results = list(results)
            for result in results:
                if field_spec is not None:
                    break
                if isinstance(result, base.Entity):
                    field_spec = result._extent.field_spec
                elif isinstance(result, base.View):
                    field_spec = result._field_spec
            if field_spec is not None:
                columns = self._get_columns_for_field_spec(field_spec)
                self.set_columns(columns)
                self.set_rows(results)

    def set_related(self, related):
        if related == self._related:
            return
        self.reset()
        if related is not None:
            extent = related.extent
            if extent is not None:
                self._extent = extent
                self._related = related
                self._row_popup_menu.set_extent(extent)
                columns = self._get_columns_for_field_spec(extent.field_spec)
                results = related.entity.sys.links(extent.name,
                                                   related.field_name)
                self.set_columns(columns)
                self.set_rows(results)

    def _after_view__row_activated(self, view, path, column):
        row = self._model[path]
        entity = row[OBJECT_COLUMN]
        if (entity is not None
            and (entity._hidden_views is None
                 or 'default' not in entity._hidden_views
                 )
            ):
            self.emit('row-activated', entity)

    def _get_columns_for_field_spec(self, field_spec):
        columns = []
        if '_oid' not in self._hidden:
            column = grid.Column('_oid', 'OID', data_type=int)
            columns.append(column)
        if '_rev' not in self._hidden:
            column = grid.Column('_rev', 'Rev', data_type=int)
            columns.append(column)
        for field_name, FieldClass in field_spec.iteritems():
            if field_name in self._hidden:
                # Don't create a column for this field.
                continue
            if self._related and field_name == self._related.field_name:
                # Don't create a column for the related field.
                continue
            if not FieldClass.expensive and not FieldClass.hidden:
                data_type = FieldClass.data_type
                title = label(FieldClass)
                if issubclass(FieldClass, field.Entity):
                    column = EntityColumn(field_name, title, data_type)
                elif issubclass(FieldClass, field.Image):
                    column = grid.Column(field_name, title, data_type,
                                         type='pixbuf')
                else:
                    column = FieldColumn(field_name, title, data_type)
                columns.append(column)
        return columns

    def _set_bindings(self):
        items = [
            ('Insert', self.select_create_action),
            ('<Control><Shift>Return', self.select_create_action),
            ('<Control>Return', self.select_update_action),
            ('Delete', self.select_delete_action),
            ]
        self._bindings = dict([(gtk.accelerator_parse(name), func)
                               for name, func in items])
        # Hack to support these with CapsLock on.
        for name, func in items:
            keyval, mod = gtk.accelerator_parse(name)
            mod = mod | gtk.gdk.LOCK_MASK
            self._bindings[(keyval, mod)] = func

type_register(EntityGrid)


class PopupMenu(grid.PopupMenu):

    def __init__(self, entity_grid):
        self._entity_grid = entity_grid
        self._extent = None
        self._entity = None
        grid.PopupMenu.__init__(self)

    def get_actions(self):
        extent = self._extent
        entity = self._entity
        items = []
        # Extent tx actions.
        actions = get_tx_actions(extent, self._entity_grid._related)
        if actions:
            if items:
                items.append(None)
            items.extend(actions)
        # Entity view actions.
        actions = get_view_actions(entity)
        if actions:
            if items:
                items.append(None)
            items.extend(actions)
        # Entity relationship actions.
        if self._entity_grid.show_relationships_in_menu:
            actions = get_relationship_actions(entity)
            if actions:
                if items:
                    items.append(None)
                items.extend(actions)
        # Entity tx actions.
        actions = get_tx_actions(entity)
        if actions:
            if items:
                items.append(None)
            items.extend(actions)
        return items

    def popup(self, event, instance):
        self.set_entity(instance)
        grid.PopupMenu.popup(self, event, instance)

    def set_entity(self, entity):
        self.clear()
        self._entity = entity
        actions = self.get_actions()
        # Create menu items.
        for action in actions:
            if action is None:
                menuitem = gtk.SeparatorMenuItem()
            else:
                menuitem = gtk.MenuItem(action.label_with_shortcut)
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
