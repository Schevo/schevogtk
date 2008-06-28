"""Schevo specific field widget classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from xml.sax.saxutils import escape
import os

if os.name == 'nt':
    import pywintypes
    import win32con
    import win32gui

import gobject
import gtk

import schevo.field
from schevo.label import label
from schevo.base import Entity
from schevo.constant import UNASSIGNED

from schevogtk2 import icon
from schevogtk2.utils import gsignal, type_register


class EntityChooser(gtk.HBox):

    __gtype_name__ = 'EntityChooser'

    gsignal('create-clicked', object, object) # allowable extent list, done_cb
    gsignal('update-clicked', object, object) # entity to update, done_cb
    gsignal('view-clicked', object) # entitiy to view
    gsignal('value-changed')

    def __init__(self, db, field, show_buttons=True):
        super(EntityChooser, self).__init__()
        self.db = db
        self.field = field
        self.props.spacing = 1
        # By default, there are no create, update or view buttons.
        self._create_button = None
        self._update_button = None
        self._view_button = None
        # Always add the combobox, allowing subclasses to specify an
        # alternate class.
        if not hasattr(self, 'EntityComboBox'):
            self.EntityComboBox = EntityComboBox
        combobox = self._entity_combobox = self.EntityComboBox(db, field)
        self.add(combobox)
        combobox.show()
        combobox.connect('value-changed', self._on_value_changed)
        # Add create/update/view buttons if the entity field allows.
        if show_buttons and isinstance(field, schevo.field.Entity):
            if field.allow_create:
                # Determine the allowed extents.
                if len(field.allow) == 0:
                    # Any extent that is not hidden, and whose create
                    # transaction is not hidden, is available.
                    allowed_extents = [
                        extent for extent in db.extents() if not extent.hidden]
                else:
                    allowed_extents = [
                        db.extent(name) for name in sorted(field.allow)]
                # Filter out extents where t.create is hidden.
                allowed_extents = self._create_button_allowed_extents = [
                    extent for extent in allowed_extents
                    if 'create' in extent.t
                    ]
                # Only create the button if there is at least one
                # allowed extent.
                if allowed_extents:
                    button = self._create_button = gtk.Button(label='+')
                    self.pack_start(button, expand=False, fill=False)
                    button.show()
                    button.props.can_focus = False
                    button.props.width_request = button.size_request()[1] * 0.8
                    button.connect('clicked', self._on_create_button__clicked)
            if field.allow_update:
                button = self._update_button = gtk.Button(label='E')
                self.pack_start(button, expand=False, fill=False)
                button.show()
                button.props.can_focus = False
                button.props.width_request = button.size_request()[1] * 0.8
                button.connect('clicked', self._on_update_button__clicked)
                # Wait before resetting sensitivity, so that the call
                # to get_selected() gets the correct selected value.
                gobject.timeout_add(0, self._reset_update_button_sensitivity)
            if field.allow_view:
                button = self._view_button = gtk.Button(label='V')
                self.pack_start(button, expand=False, fill=False)
                button.show()
                button.props.can_focus = False
                button.props.width_request = button.size_request()[1] * 0.8
                button.connect('clicked', self._on_view_button__clicked)
                # Wait before resetting sensitivity, so that the call
                # to get_selected() gets the correct selected value.
                gobject.timeout_add(0, self._reset_view_button_sensitivity)

    def get_selected(self):
        """Return the currently selected Schevo object."""
        return self._entity_combobox.get_selected()

    def select_item_by_data(self, data):
        return self._entity_combobox.select_item_by_data(data)

    def _on_create_button__clicked(self, widget):
        db = self.db
        field = self.field
        self.emit('create-clicked', self._create_button_allowed_extents, None)
        # New field value may have side-effects.
        self._on_value_changed(self)

    def _on_update_button__clicked(self, widget):
        entity_to_update = self.get_selected()
        self.emit('update-clicked', entity_to_update, None)
        # New field value may have side-effects.
        self._on_value_changed(self)

    def _on_value_changed(self, widget):
        self.emit('value-changed')
        self._reset_update_button_sensitivity()
        self._reset_view_button_sensitivity()

    def _on_view_button__clicked(self, widget):
        entity_to_view = self.get_selected()
        self.emit('view-clicked', entity_to_view)

    def _reset_update_button_sensitivity(self):
        """Update the `_update_button` sensitivity based on whether or
        not the current value of the combobox allows updating."""
        button = self._update_button
        if button is not None:
            selected = self.get_selected()
            # UNASSIGNED.
            if selected is UNASSIGNED:
                button.set_sensitive(False)
            # Entity.
            elif isinstance(selected, Entity):
                button.set_sensitive('update' in selected.t)

    def _reset_view_button_sensitivity(self):
        """Update the `_view_button` sensitivity based on whether or
        not the current value of the combobox allows viewing."""
        button = self._view_button
        if button is not None:
            selected = self.get_selected()
            # UNASSIGNED.
            if selected is UNASSIGNED:
                button.set_sensitive(False)
            # Entity.
            elif isinstance(selected, Entity):
                button.set_sensitive('update' in selected.t)

type_register(EntityChooser)


class BaseComboBox(gtk.ComboBoxEntry):
    """Base class for common behavior."""

    gsignal('value-changed')

    # Label to use for UNASSIGNED values.  Useful if you want to make
    # the combo box more visually descriptive in the face of such
    # values.
    unassigned_label = '<UNASSIGNED>'

    def __init__(self):
        gtk.ComboBoxEntry.__init__(self)
        self.model = gtk.ListStore(str, object)
        self._populate()
        self.set_model(self.model)
        self.set_row_separator_func(self.is_row_separator)
        # Set the column that the combo box entry will search for text
        # within.
        self.set_text_column(0)
        # Set renderers.
        cell = self.cell_pb = gtk.CellRendererPixbuf()
        self.pack_start(cell, False)
        self.set_cell_data_func(cell, self.cell_icon)
        # Move the pixbuf cell to the zeroth column so it shows up in
        # the correct location.
        self.reorder(cell, 0)
        # Set up the completion widget.
        self.completion = comp = gtk.EntryCompletion()
        comp.set_model(self.model)
        cell = self.comp_pb = gtk.CellRendererPixbuf()
        comp.pack_start(cell, False)
        comp.set_cell_data_func(cell, self.cell_icon)
        comp.set_inline_selection(True)
##         comp.set_match_func(self._on_completion__is_match)
        comp.set_text_column(0)
        self.entry = entry = self.child
        entry.set_completion(comp)
        # Only set focus on the entry, skipping past the arrow button.
        self.set_focus_chain([entry])
##         entry.connect('activate', self._on_entry__activate)
        self.connect('changed', self._on_entry__changed)
        # Prevent the changed handler from being called recursively.
        self._handling_changed = False
        entry.connect_after('insert-text', self._on_entry__insert_text)
        # Prevent the insert-text handler from being called recursively.
        self._handling_insert_text = False

    def get_selected(self):
        """Return the currently selected Schevo object."""
        iter = self.get_active_iter()
        if iter:
            return self.model[iter][1]

    def is_row_separator(self, model, row):
        text, entity = model[row]
        if text is None and entity is None:
            return True
        return False

    def select_item_by_text(self, text):
        for row in self.model:
            if row[0] == text:
                self._handling_changed = True
                self.set_active_iter(row.iter)
                self._handling_changed = False
                return
        # Not in the combo box, so select nothing
        self.set_active(-1)

    def select_item_by_data(self, data):
        for row in self.model:
            if row[1] == data:
                self._handling_changed = True
                self.set_active_iter(row.iter)
                self._handling_changed = False
                return
        # Not in the combo box, so select nothing
        self.set_active(-1)

##     def _on_entry__activate(self, entry):
##         self.emit('activate')

    def _on_entry__changed(self, widget):
        if self._handling_changed:
            return
        entry = self.entry
        entry_text = entry.get_text()
        self._handling_changed = True
        self.select_item_by_text(entry_text)
        self._handling_changed = False
        self.emit('value-changed')

    def _on_entry__insert_text(self, entry, new_text, new_text_len, position):
        if self._handling_changed:
            return
        if self._handling_insert_text:
            return
        if self.get_selected() is not None:
            return
        # Get the full text of the Entry widget, and see if any
        # strings in the model begin with that text.
        entry_text = entry.get_text()
        entry_text_lower = entry_text.lower()
        matching_rows = [
            # row,
            ]
        for row in self.model:
            row_text = row[0]
            if isinstance(row_text, basestring):
                if row[0].lower().startswith(entry_text_lower):
                    matching_rows.append(row)
        # If there is one and only one such string,
        if len(matching_rows) == 1:
            row = matching_rows[0]
            # Stop the insert-text signal from further emission until
            # we're done. For some reason, storing the handler_id of
            # the connect_after call in __init__ does not work
            # properly to keep this from being called recursively, so
            # we used a _handling_insert_text flag instead.
            self._handling_insert_text = True
            try:
                # Set the entry's text to that string.
                entry.set_text(row[0])
                # Select the portion of the string that the user
                # didn't type.  Use a timeout, since select_region
                # doesn't work properly within a signal handler.
                def select_region():
                    start = len(entry_text)
                    entry.select_region(start, -1)
                    # Destroy the timer immediately.
                    return False
                gobject.timeout_add(0, select_region)
            finally:
                # Done, so allow insert-text signal to be emitted again.
                self._handling_insert_text = False


class EntityComboBox(BaseComboBox):
    """ComboBoxEntry for displaying entities allowed by a field."""

    __gtype_name__ = 'EntityComboBox'

    # Function to create a label for an entity. By default, just use
    # the unicode representation of the entity.
    entity_label = unicode

    def __init__(self, db, field):
        self.db = db
        self.field = field
        super(EntityComboBox, self).__init__()
        # Select the field's current item.
        self.select_item_by_data(field.get())

    def cell_icon(self, layout, cell, model, row):
        entity = model[row][1]
        if entity in (UNASSIGNED, None):
            cell.set_property('stock_id', gtk.STOCK_NO)
            cell.set_property('stock_size', gtk.ICON_SIZE_SMALL_TOOLBAR)
            cell.set_property('visible', False)
        else:
            extent = entity.sys.extent
            pixbuf = icon.small_pixbuf(self, extent)
            cell.set_property('pixbuf', pixbuf)
            cell.set_property('visible', True)

    def _populate(self):
        db = self.db
        field = self.field
        allow = field.allow
        entity_label = self.entity_label
        if len(allow) > 1:
            allow_multiple = True
        else:
            allow_multiple = False
        items = []
        values = []
        # Unassigned.
        items.append((self.unassigned_label, UNASSIGNED))
        values.append(UNASSIGNED)
        # Preferred values.
        preferred_values = field.preferred_values or []
        if preferred_values:
            values.extend(preferred_values)
            more = []
            for entity in sorted(preferred_values):
                if entity is UNASSIGNED:
                    continue
                if allow_multiple:
                    extent_text = label(entity.sys.extent)
                    text = u'%s :: %s' % (entity_label(entity), extent_text)
                else:
                    text = u'%s' % (entity_label(entity), )
                more.append((text, entity))
            items.extend(more)
            # Row separator.
            items.append((None, None))
        # Valid values.
        more = []
        valid_values = field.valid_values
        if valid_values is not None:
            # Specific valid values.
            values.extend(valid_values)
            for entity in sorted(valid_values):
                if entity is UNASSIGNED:
                    continue
                if entity in preferred_values:
                    continue
                if allow_multiple:
                    extent_text = label(entity.sys.extent)
                    text = u'%s :: %s' % (entity_label(entity), extent_text)
                else:
                    text = u'%s' % (entity_label(entity), )
                more.append((text, entity))
        else:
            # Other allowed values.
            for extent_name in field.allow:
                extent = db.extent(extent_name)
                for entity in sorted(extent):
                    if entity in preferred_values:
                        continue
                    values.append(entity)
                    if allow_multiple:
                        extent_text = label(extent)
                        text = u'%s :: %s' % (entity_label(entity), extent_text)
                    else:
                        text = u'%s' % (entity_label(entity), )
                    more.append((text, entity))
        items.extend(more)
        value = field.get()
        if value not in values:
            entity = value
            # Row separator.
            items.append((None, None))
            # Invalid, but current value.
            if allow_multiple:
                extent_text = label(entity.sys.extent)
                text = u'%s :: %s' % (entity_label(entity), extent_text)
            else:
                text = u'%s' % (entity_label(entity), )
            items.append((text, entity))
        # Update the model.
        model = self.model
        model.clear()
        for text, entity in items:
            model.append((text, entity))

type_register(EntityComboBox)


class ExtentComboBox(BaseComboBox):
    """ComboBoxEntry for displaying one or more extents."""

    # XXX: This is not used by DynamicField, since there is no
    # f.extent() field type in Schevo at this point. It is here so
    # those applications that wish to have an extent combo box may use
    # a central base class.

    __gtype_name__ = 'ExtentComboBox'

    def __init__(self, db, field):
        self.db = db
        # XXX: Field is currently unused.
        super(ExtentComboBox, self).__init__()
        # Initially, select no extent.
        self.select_item_by_data(UNASSIGNED)

    def allowed_extents(self):
        """Return the allowed extents.

        Override in a subclass to limit to only a few extents rather
        than all extents in the database.
        """
        return self.db.extents()

    def cell_icon(self, layout, cell, model, row):
        extent = model[row][1]
        if extent in (UNASSIGNED, None):
            cell.set_property('stock_id', gtk.STOCK_NO)
            cell.set_property('stock_size', gtk.ICON_SIZE_SMALL_TOOLBAR)
            cell.set_property('visible', False)
        else:
            pixbuf = icon.small_pixbuf(self, extent)
            cell.set_property('pixbuf', pixbuf)
            cell.set_property('visible', True)

    def extent_label(self, extent):
        return label(extent)

    def _populate(self):
        db = self.db
        model = self.model
        model.clear()
        model.append((self.unassigned_label, UNASSIGNED))
        model.append((None, None))
        for extent_name in sorted(self.allowed_extents()):
            extent = db.extent(extent_name)
            model.append((self.extent_label(extent), extent))

type_register(ExtentComboBox)


class FileChooser(gtk.EventBox):

    __gtype_name__ = 'FileChooser'

    gsignal('value-changed')

    def __init__(self, db, field):
        super(FileChooser, self).__init__()
        self.set_visible_window(False)
        self.db = db
        self.field = field
        if os.name == 'nt' and not field.directory_only:
            if field.file_only:
                stock_id = gtk.STOCK_FILE
##             elif field.directory_only:
##                 stock_id = gtk.STOCK_DIRECTORY
            self._hbox = hbox = gtk.HBox()
            hbox.show()
            self._entry = entry = gtk.Entry()
            entry.show()
            self._button = button = gtk.Button()
            button.show()
            image = gtk.Image()
            image.show()
            image.set_from_stock(stock_id, gtk.ICON_SIZE_MENU)
            button.add(image)
            hbox.pack_start(entry)
            hbox.pack_start(button, expand=False)
            button.connect('clicked', self._on_clicked)
            entry.connect('activate', self._on_changed)
            self.add(hbox)
        else:
            title = 'Choose %r file' % label(self.field)
            self._filechooser = chooser = gtk.FileChooserButton(title)
            if self.field.directory_only:
                chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
            chooser.show()
            chooser.connect('selection-changed', self._on_changed)
            self.add(chooser)

    def get_filename(self):
        if os.name == 'nt' and not self.field.directory_only:
            return self._entry.get_text()
        else:
            return self._filechooser.get_filename()

    def set_filename(self, filename):
        if os.name == 'nt' and not self.field.directory_only:
            self._entry.set_text(filename)
        else:
            return self._filechooser.set_filename(filename)

    def _on_changed(self, widget):
        self.emit('value-changed')

    def _on_clicked(self, widget):
        field = self.field
        filename = None
        file_ext_filter = 'Schevo Database Files\0*.db;*.schevo\0'
        file_custom_filter = 'All Files\0*.*\0'
        file_open_title = 'Select File'
        if field.file_only:
            try:
                filename, custom_filter, flags = win32gui.GetSaveFileNameW(
                    InitialDir='.',
                    Flags=win32con.OFN_EXPLORER,
                    Title='Select'
##                     File='',
##                     DefExt='',
##                     Title=self.file_open_title,
##                     Filter=self.file_ext_filter,
##                     CustomFilter=self.file_custom_filter,
##                     FilterIndex=1,
                    )
            except pywintypes.error:
                # Cancel button raises an exception.
                pass
        elif field.directory_only:
            try:
                filename, custom_filter, flags = win32gui.GetSaveFileNameW(
                    InitialDir='.',
                    Flags=win32con.OFN_EXPLORER,
                    Title='Select'
##                     File='',
##                     DefExt='',
##                     Title=self.file_open_title,
##                     Filter=self.file_ext_filter,
##                     CustomFilter=self.file_custom_filter,
##                     FilterIndex=1,
                    )
            except pywintypes.error:
                # Cancel button raises an exception.
                pass
        if filename is not None:
            self.set_filename(filename)

type_register(FileChooser)


class ValueChooser(gtk.HBox):

    __gtype_name__ = 'ValueChooser'

    gsignal('value-changed')

    def __init__(self, db, field):
        super(ValueChooser, self).__init__()
        self.db = db
        self.field = field
        # Always add the combobox.
        combobox = self._value_combobox = ValueComboBox(db, field)
        self.add(combobox)
        combobox.show()
        combobox.connect('value-changed', self._on_value_changed)

    def get_selected(self):
        """Return the currently selected Schevo object."""
        return self._value_combobox.get_selected()

    def _on_value_changed(self, widget):
        self.emit('value-changed')

type_register(ValueChooser)


class ValueComboBox(BaseComboBox):

    __gtype_name__ = 'ValueComboBox'

    def __init__(self, db, field):
        self.db = db
        self.field = field
        super(ValueComboBox, self).__init__()
        # Select the field's current item.
        self.select_item_by_data(field.get())

    def cell_icon(self, layout, cell, model, row):
        cell.set_property('stock_id', gtk.STOCK_NO)
        cell.set_property('stock_size', gtk.ICON_SIZE_SMALL_TOOLBAR)
        cell.set_property('visible', False)

    def _populate(self):
        db = self.db
        field = self.field
        items = []
        values = []
        # Unassigned.
        items.append((self.unassigned_label, UNASSIGNED))
        values.append(UNASSIGNED)
        # Preferred values.
        preferred_values = field.preferred_values or []
        if preferred_values:
            values.extend(preferred_values)
            more = []
            for value in sorted(preferred_values):
                if value is UNASSIGNED:
                    continue
                more.append((unicode(value), value))
            items.extend(more)
            # Row separator.
            items.append((None, None))
        # Valid values.
        more = []
        valid_values = field.valid_values
        values.extend(valid_values)
        for value in sorted(valid_values):
            if value is UNASSIGNED:
                continue
            if value in preferred_values:
                continue
            more.append((unicode(value), value))
        items.extend(more)
        value = field.get()
        if value not in values:
            # Row separator.
            items.append((None, None))
            # Invalid, but current value.
            items.append((unicode(value), value))
        # Update the model.
        model = self.model
        model.clear()
        for text, value in items:
            model.append((text, value))

type_register(ValueComboBox)


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
