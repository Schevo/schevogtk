"""Grid widget.

For copyright, license, and warranty, see bottom of file.
"""

import gc
import datetime
import sys
from schevo.lib import optimize

from schevo.error import EntityDoesNotExist

import gtk
from gtk import gdk

from schevogtk2.utils import gproperty, gsignal, type_register


WATCH = gdk.Cursor(gdk.WATCH)

OBJECT_COLUMN = 0
COLOR_COLUMN = 1
STRIKETHROUGH_COLUMN = 2


class Column(object):

    get_attribute = getattr
    justify = gtk.JUSTIFY_LEFT
    visible = True
    width = None

    _has_icon = False
    _style = gtk.Style()

    def __init__(self, grid, attribute, title, data_type,
                 type='text', call=False):
        self.grid = grid
        self.attribute = attribute
        self.title = title
        self.data_type = data_type
        self.type = type
        self.call = call
        if data_type in (int, float):
            self.justify = gtk.JUSTIFY_RIGHT
        if type == 'pixbuf':
            self.cell = gtk.CellRendererPixbuf()
            self.cell_prop = 'pixbuf'
        elif type == 'text':
            self.cell = gtk.CellRendererText()
            self.cell_prop = 'text'
        elif type == 'toggle':
            self.cell = gtk.CellRendererToggle()
            self.cell_prop = 'active'

    def cell_data(self, column, cell, model, row_iter):
        instance = model[row_iter][OBJECT_COLUMN]
        color = model[row_iter][COLOR_COLUMN]
        limits = self.grid.limit_row_background_color
        if limits is not None and self.attribute in limits:
            cell.set_property('cell-background', color)
        strikethrough = model[row_iter][STRIKETHROUGH_COLUMN]
        cell.set_property('strikethrough', strikethrough)
        try:
            data = self.cell_data_getattr(instance, self.attribute)
        except EntityDoesNotExist:
            data = None
        if self.call:
            data = data()
        prop = self.cell_prop
        if data is not None:
            if prop == 'text':
                data = unicode(data)
            elif prop == 'pixbuf':
                loader = gtk.gdk.PixbufLoader()
                loader.write(data)
                loader.close()
                data = loader.get_pixbuf()
            elif prop == 'active':
                data = bool(data)
        cell.set_property(prop, data)

    cell_data_getattr = staticmethod(getattr)

    def cell_icon(self, column, cell, model, row_iter):
        instance = model[row_iter][OBJECT_COLUMN]
        color = model[row_iter][COLOR_COLUMN]
        limits = self.grid.limit_row_background_color
        if limits is not None and self.attribute in limits:
            cell.set_property('cell-background', color)

    def create_column(self, grid):
        self.is_row_strikethrough = grid.is_row_strikethrough
        justify = self.justify
        if justify == gtk.JUSTIFY_LEFT:
            xalign = 0.0
        elif justify == gtk.JUSTIFY_CENTER:
            xalign = 0.5
        elif justify == gtk.JUSTIFY_RIGHT:
            xalign = 1.0
        else:
            raise ValueError('%r value for justify is not valid.' % (justify))
        self.cell.set_property('xalign', xalign)
        column = gtk.TreeViewColumn(self.title)
        column.set_resizable(True)
        column.set_reorderable(True)
        column.set_property('alignment', xalign)
        if self._has_icon:
            self._pack_icon(column)
        else:
            self._pack(column)
        column.set_visible(self.visible)
        if self.width is not None:
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column.set_fixed_width(self.width)
##         if self.searchable:
##             view.set_search_column(index)
##             view.set_search_equal_func(view_search_equal_func, column)
        return column

    @classmethod
    def get_style(cls):
        return cls._style

    def _pack(self, column):
        """Pack one or more renderers into the column."""
        cell = self.cell
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data)

    def _pack_icon(self, column):
        """Pack one or more renderers into the column."""
        # Icon.
        cell = self.cell_pb = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.set_cell_data_func(cell, self.cell_icon)
        # Standard renderer.
        cell = self.cell
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data)


class Grid(gtk.VBox):

    __gtype_name__ = 'Grid'

    gsignal('row-activated', object)

    gsignal('selection-changed', object)

    limit_row_background_color = None

    search_equal_func = None

    def __init__(self, columns=[]):
        gtk.VBox.__init__(self)
        self.props.spacing = 5
        # Create find text entry.  Hide it at first.
        find_entry_box = self._find_entry_box = gtk.HBox()
        find_entry_box.props.spacing = 5
        find_entry_box.hide()
        self.pack_start(find_entry_box, expand=False)
        find_entry_label = gtk.Label('Find:')
        find_entry_label.show()
        find_entry_box.pack_start(find_entry_label, expand=False)
        find_entry = self._find_entry = gtk.Entry()
        find_entry.show()
        find_entry_box.pack_start(find_entry)
        # Create scrolled window and rest of grid.
        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scrolled.show()
        self.pack_start(scrolled)
        self._bindings = {}
        self._columns = []
        self._filter = None
        self._sorter = None
        self._row_map = {}
        self._row_popup_menu = None
        self._model = model = gtk.ListStore(object, object, object)
        model.set_default_sort_func(model_default_sort)
        self._view = view = gtk.TreeView(model)
        view.connect(
            'button-press-event', self._on_view__button_press_event)
        view.connect(
            'button-release-event', self._on_view__button_release_event)
        view.connect_after(
            'key-press-event', self._after_view__key_press_event)
        view.connect('popup-menu', self._on_view__popup_menu)
        view.connect_after('row-activated', self._after_view__row_activated)
        view.set_rules_hint(True)
        view.show()
        scrolled.add(view)
        self.set_columns(columns)
        selection = view.get_selection()
        selection.connect('changed', self._on_selection__changed)
        self.set_selection_mode(gtk.SELECTION_BROWSE)

    def add_row(self, instance):
        color = self.row_background_color(instance)
        strikethrough = self.is_row_strikethrough(instance)
        row_iter = self._model.append((instance, color, strikethrough))
        return row_iter

    def clear(self):
        """Removes all the instances of the list"""
        self._model.clear()
        self._row_map.clear()

    def get_selected(self):
        """If in multiple selection mode, return a list of the
        currently selected objects.  If not, return the currently
        selected object or None if none selected."""
        selection = self._view.get_selection()
        if selection.get_mode() != gtk.SELECTION_MULTIPLE:
            model, row_iter = selection.get_selected()
            if row_iter:
                return model[row_iter][OBJECT_COLUMN]
        else:
            selection = self._view.get_selection()
            model, rows = selection.get_selected_rows()
            return [model[row][OBJECT_COLUMN] for row in rows]

    def is_row_strikethrough(self, instance):
        return False

    def redraw(self):
        """Resets color and strikethrough values."""
        model = self._model
        for row in model:
            instance = row[OBJECT_COLUMN]
            try:
                color = self.row_background_color(instance)
            except EntityDoesNotExist:
                color = None
            row[COLOR_COLUMN] = color
            try:
                strikethrough = self.is_row_strikethrough(instance)
            except EntityDoesNotExist:
                strikethrough = False
            row[STRIKETHROUGH_COLUMN] = strikethrough

    def refilter(self):
        if self._filter is not None:
            self._filter.refilter()

    def row_background_color(self, instance):
        return None

    def select(self, instance, scroll=True):
        model = self._model
        view = self._view
        selection = view.get_selection()
        inst_id = self.identify(instance)
        row_iter = self._row_map[inst_id]
        if row_iter in model:
            selection.select_iter(row_iter)
            if scroll:
                self.select_and_focus_row(row_iter)
##                 view.scroll_to_cell(model[row_iter].path, None, True, 0.5, 0)

    def select_and_focus_row(self, row_iter):
        self._view.set_cursor(self._model[row_iter].path)

    def set_columns(self, columns, spacer=True):
        # Reset sorting back to the default.
        self._model.set_sort_column_id(-1, gtk.SORT_ASCENDING)
        # Use a sort model if one was defined.
        if self._sorter is not None:
            model = self._sorter
        else:
            model = self._model
        view = self._view
        # Remove any existing columns.
        for column in view.get_columns():
            view.remove_column(column)
        # Create new columns.
        self._columns = columns
        for index, column in enumerate(columns):
            model.set_sort_func(index, model_sort, (column, column.attribute))
            view_column = column.create_column(self)
            view_column.set_sort_column_id(index)
            view.append_column(view_column)
        # One additional column to take up any remaining space.
        if spacer:
            view_column = gtk.TreeViewColumn()
            view_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            view_column.set_fixed_width(1)
            view.append_column(view_column)

    def set_cursor(self, cursor=None):
        window = self.window
        # Since a ScrolledWindow doesn't have an X window this window
        # will be the same as this widget's parent window.
        if window is not None:
            window.set_cursor(cursor)

##     def identify(self, instance):
##         return hash(instance)

    identify = hash  # Overridden in subclasses.

    def set_rows(self, instances):
        self.set_cursor(WATCH)
        view = self._view
        view.freeze_notify()
        view.set_model(None)
        self.unselect_all()
        self.clear()
        gc.collect()
        model = self._model
        identify = self.identify
        row_map = self._row_map
        insert = model.insert
        n = 0
        for instance in instances:
            inst_id = identify(instance)
            color = self.row_background_color(instance)
            strikethrough = self.is_row_strikethrough(instance)
            row_iter = insert(n, (instance, color, strikethrough))
            row_map[inst_id] = row_iter
            n += 1
        if self._sorter is not None:
            view.set_model(self._sorter)
        else:
            view.set_model(model)
        view.thaw_notify()
        self.set_cursor()

    def set_search_equal_func(self, search_equal_func):
        view = self._view
        entry_box = self._find_entry_box
        entry = self._find_entry
        view.set_search_equal_func(search_equal_func)
        view.props.enable_search = True
        view.set_search_equal_func(search_equal_func)
        view.set_search_entry(entry)
        entry_box.show()
        entry.grab_focus()

    def get_selection_mode(self):
        return self._view.get_selection().get_mode()

    def set_selection_mode(self, mode):
        self._view.get_selection().set_mode(mode)

    def set_visible_func(self, func, data=None):
        self._filter = self._model.filter_new()
        if data is None:
            self._filter.set_visible_func(func)
        else:
            self._filter.set_visible_func(func, data)
        self._sorter = gtk.TreeModelSort(self._filter)

    def unselect_all(self):
        selection = self._view.get_selection()
        if selection:
            selection.unselect_all()

    # Event handlers ---------------------------------------------------------

    def _after_view__key_press_event(self, widget, event):
        keyval = event.keyval
        mask = event.state & gdk.MODIFIER_MASK
        binding = (keyval, mask)
        if binding in self._bindings:
            func = self._bindings[binding]
            func()

    def _after_view__row_activated(self, view, path, column):
        row = self._model[path]
        item = row[OBJECT_COLUMN]
        self.emit('row-activated', item)

    def _on_selection__changed(self, selection):
        """Transform selection::changed into selection-changed."""
        item = self.get_selected()
        self.emit('selection-changed', item)

    def _on_view__button_press_event(self, view, event):
        if self.get_selection_mode() == gtk.SELECTION_MULTIPLE:
            if event.button == 3 and self._row_popup_menu is not None:
                # Determine if mouse cursor is over a selected item.
                #
                # If it is, do not allow the event to propagate, so
                # that the current multiselection is kept.
                #
                # If not, allow the event to propagate, so that the
                # non-selected item is selected before the menu
                # appears.
                x, y = event.get_coords()
                path = view.get_path_at_pos(int(x), int(y))
                if path is not None:
                    path, col, cell_x, cell_y = path
                    row = self._model[path]
                    item = row[OBJECT_COLUMN]
                    cursor_over_selected_item = item in self.get_selected()
                    return cursor_over_selected_item
                else:
                    # Not over any row; allow event to propagate.
                    return False

    def _on_view__button_release_event(self, view, event):
        if event.button == 3 and self._row_popup_menu is not None:
            instance = self.get_selected()
            if isinstance(instance, list):
                if len(instance) == 1:
                    instance = instance[0]
                else:
                    instance = None
            self._row_popup_menu.popup(event, instance)

    def _on_view__popup_menu(self, view):
        if self._row_popup_menu is not None:
            event = None
            instance = self.get_selected()
            if isinstance(instance, list):
                if len(instance) == 1:
                    instance = instance[0]
                else:
                    instance = None
            self._row_popup_menu.popup(event, instance)
            return True

    def _on_view__start_interactive_search(self, view):
        self._find_entry.show()
        self._find_entry.grab_focus()


type_register(Grid)


class PopupMenu(gtk.Menu):

    def __init__(self):
        self._instance = None
        self._signals = []
        gtk.Menu.__init__(self)

    def clear(self):
        self._instance = None
        for child in self:
            self.remove(child)
        for menuitem, signal_id in self._signals:
            menuitem.disconnect(signal_id)
        self._signals = []

    def popup(self, event, instance):
        self._instance = instance
        if len(self):
            if event is None:
                # Note: button = 1, and time = 0 is a known gtk+ hack.
                gtk.Menu.popup(self, None, None, None, 1, 0)
            else:
                gtk.Menu.popup(self, None, None, None, event.button, event.time)


def model_default_sort(model, row_iter1, row_iter2):
    instance1 = model[row_iter1][OBJECT_COLUMN]
    instance2 = model[row_iter2][OBJECT_COLUMN]
    return cmp(instance1, instance2)

def model_sort(model, row_iter1, row_iter2, (column, attr_name)):
    instance1 = model[row_iter1][OBJECT_COLUMN]
    instance2 = model[row_iter2][OBJECT_COLUMN]
    get_attribute = column.get_attribute
    attr1 = get_attribute(instance1, attr_name)
    attr2 = get_attribute(instance2, attr_name)
    if isinstance(attr1, datetime.date):
        attr1 = attr1.timetuple()
    if isinstance(attr2, datetime.date):
        attr2 = attr2.timetuple()
    return cmp((attr1, instance1), (attr2, instance2))


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
