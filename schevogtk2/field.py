"""Schevo field widgets.

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

import gtk
import pango

import schevo.field
from schevo.label import label
from schevo.base import Transaction
from schevo.constant import UNASSIGNED

from schevogtk2 import icon
from schevogtk2.utils import gsignal, type_register


MONO_FONT = pango.FontDescription('monospace normal')


class DynamicField(gtk.EventBox):

    __gtype_name__ = 'DynamicField'

    gsignal('value-changed')

    def __init__(self):
        super(DynamicField, self).__init__()
        widget = gtk.Entry()
        widget.show()
        self.add(widget)
        self._db = None
        self._field = None
        self.expand = False

    def get_value(self):
        widget = self.child
        if isinstance(widget, gtk.ScrolledWindow):
            widget = widget.child
        if isinstance(widget, gtk.CheckButton):
            value = widget.get_active()
        elif isinstance(widget, FileChooser):
            value = widget.get_filename()
        elif isinstance(widget, gtk.Image):
            # XXX Hack since images can't be edited.
            value = self._field.get()
        elif isinstance(widget, EntityChooser):
            value = widget.get_selected()
            if value is None:
                value = UNASSIGNED
        elif isinstance(widget, gtk.TextView):
            text_buffer = widget.props.buffer
            startiter, enditer = text_buffer.get_bounds()
            value = text_buffer.get_text(startiter, enditer)
            if not value:
                value = UNASSIGNED
        elif isinstance(widget, ValueChooser):
            value = widget.get_selected()
            if value is None:
                value = UNASSIGNED
        else:
            value = widget.get_text()
            if not value:
                value = UNASSIGNED
        return value

    def reset(self):
        self.set_field(self._db, self._field)

    def set_field(self, db, field):
        self._db = db
        self._field = field
        self.remove(self.child)
        control = None  # Defaults to the widget.
        value = field.get()
        # Calculated field.
        if field.fget:
            if value is UNASSIGNED:
                value = ''
            else:
                value = unicode(value)
            widget = gtk.Entry()
            widget.set_text(value)
        # Boolean.
        elif isinstance(field, schevo.field.Boolean) and not field.readonly:
            widget = gtk.CheckButton()
            if value is UNASSIGNED:
                value = False
            widget.set_active(value)
            widget.set_label(unicode(value))
            def on_toggled(widget):
                widget.set_label(unicode(widget.get_active()))
            widget.connect('toggled', on_toggled)
            widget.connect('toggled', self._on_widget__value_changed, field)
        # Entity.
        elif isinstance(field, schevo.field.Entity) and not field.readonly:
            widget = EntityChooser(db, field)
            widget.connect('changed',
                           self._on_widget__value_changed, field)
        # Image.
        elif isinstance(field, schevo.field.Image):
            widget = gtk.Image()
            if value is not UNASSIGNED:
                loader = gtk.gdk.PixbufLoader()
                loader.write(value)
                loader.close()
                pixbuf = loader.get_pixbuf()
                widget.set_from_pixbuf(pixbuf)
        # Memo.
        elif isinstance(field, schevo.field.Memo):
            self.expand = True
            if value is UNASSIGNED:
                value = ''
            else:
                value = unicode(value)
            widget = gtk.ScrolledWindow()
            widget.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
            widget.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            control = textview = gtk.TextView()
            if field.monospace:
                textview.modify_font(MONO_FONT)
            textview.set_accepts_tab(False)
            textview.show()
            textview.set_size_request(-1, 150)
            textbuff = textview.props.buffer
            textbuff.set_text(value)
##             textbuff.connect('changed', self._on_widget__value_changed, field)
            widget.add(textview)
        # Path.
        elif isinstance(field, schevo.field.Path) and not field.readonly:
            widget = FileChooser(db, field)
            if value:
                widget.set_filename(value)
            widget.connect('value-changed',
                           self._on_widget__value_changed, field)
        # All other field types.
        else:
            # Valid values combo box.
            if field.valid_values is not None:
                widget = ValueChooser(db, field)
                widget.connect('changed',
                               self._on_widget__value_changed, field)
            else:
                if value is UNASSIGNED:
                    value = ''
                else:
                    value = unicode(value)
                widget = gtk.Entry()
                widget.set_text(value)
                widget.connect('activate',
                               self._on_widget__value_changed, field)
##         data_type = field.data_type
##         widget.set_property('data-type', data_type)
##         widget.set_property('model_attribute', field.name)
        if control is None:
            control = widget
        if field.fget or field.readonly:
            if hasattr(control, 'set_editable'):
                control.set_editable(False)
            if hasattr(control.props, 'can-focus'):
                control.props.can_focus = False
            if hasattr(control.props, 'has-focus'):
                control.props.has_focus = False
            if hasattr(control, 'set_sensitive'):
                control.set_sensitive(False)
##             if hasattr(control, 'set_selectable'):  # Label only.
##                 control.set_selectable(True)
        widget.show()
        self.add(widget)

    def _on_widget__value_changed(self, widget, field):
        value = self.get_value()
##         print '%s changed to: %s %r:' % (field.name, value, value)
        self.emit('value-changed')

type_register(DynamicField)


class EntityChooser(gtk.ComboBox):

    __gtype_name__ = 'EntityChooser'

    gsignal('value-changed')

    def __init__(self, db, field):
        super(EntityChooser, self).__init__()
        self.db = db
        self.field = field
        self.model = gtk.ListStore(str, object)
        self.set_row_separator_func(self.is_row_separator)
        self._populate()
        self.set_model(self.model)
##         self.set_text_column(0)
        cell = self.cell_pb = gtk.CellRendererPixbuf()
        self.pack_start(cell, False)
        self.set_cell_data_func(cell, self.cell_icon)
##         self.reorder(cell, 0)
        cell = self.cell_text = gtk.CellRendererText()
        self.pack_start(cell)
        self.add_attribute(cell, 'text', 0)
##         self.completion = comp = gtk.EntryCompletion()
##         comp.set_model(self.model)
##         cell = self.comp_pb = gtk.CellRendererPixbuf()
##         comp.pack_start(cell, False)
##         comp.set_cell_data_func(cell, self.cell_icon)
##         comp.set_text_column(0)
##         self.entry = entry = self.child
##         entry.set_completion(comp)
##         entry.set_text(str(field.get()))
##         entry.connect('activate', self._on_entry__activate)
##         entry.connect('changed', self._on_entry__changed)
        self.select_item_by_data(field.get())
        self.connect('changed', self._on_changed)

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

    def get_selected(self):
        iter = self.get_active_iter()
        if iter:
            return self.model[iter][1]

    def is_row_separator(self, model, row):
        text, entity = model[row]
        if text is None and entity is None:
            return True
        return False

    def select_item_by_data(self, data):
        for row in self.model:
            if row[1] == data:
                self.set_active_iter(row.iter)
                break

    def _on_changed(self, widget):
        self.emit('value-changed')

##     def _on_entry__activate(self, entry):
##         self.emit('activate')

##     def _on_entry__changed(self, entry):
##         self.emit('value-changed')

    def _populate(self):
        db = self.db
        field = self.field
        allow = field.allow
        if len(allow) > 1:
            allow_multiple = True
        else:
            allow_multiple = False
        items = []
        values = []
        # Unassigned.
        items.append((u'<UNASSIGNED>', UNASSIGNED))
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
                    text = u'%s :: %s' % (entity, extent_text)
                else:
                    text = u'%s' % (entity, )
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
                    text = u'%s :: %s' % (entity, extent_text)
                else:
                    text = u'%s' % (entity, )
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
                        text = u'%s :: %s' % (entity, extent_text)
                    else:
                        text = u'%s' % (entity, )
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
                text = u'%s :: %s' % (entity, extent_text)
            else:
                text = u'%s' % (entity, )
            items.append((text, entity))
        # Update the model.
        model = self.model
        model.clear()
        for text, entity in items:
            model.append((text, entity))

type_register(EntityChooser)


class FieldLabel(gtk.EventBox):

    __gtype_name__ = 'FieldLabel'

    def __init__(self):
        super(FieldLabel, self).__init__()
        text = u'Field label:'
        label = gtk.Label()
        label.set_text(text)
        label.set_alignment(1.0, 0.5)
        label.set_padding(5, 0)
        label.show()
        self.add(label)

    def set_field(self, db, field):
        label = self.child
        text = field.label
        if field.readonly:
            pattern = u'%s:'
        else:
            pattern = u'<b>%s:</b>'
        if (not field.fget and field.required
            and isinstance(field.instance, Transaction)):
            text = '* ' + text
        markup = pattern % escape(text)
        label.set_markup(markup)

type_register(FieldLabel)


class FileChooser(gtk.EventBox):

    __gtype_name__ = 'FileChooser'

    gsignal('value-changed')

    def __init__(self, db, field):
        super(FileChooser, self).__init__()
        self.db = db
        self.field = field
        if os.name == 'nt':
            if field.file_only:
                stock_id = gtk.STOCK_FILE
            elif field.directory_only:
                stock_id = gtk.STOCK_DIRECTORY
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
            self._filechooser = chooser = gtk.FileChooserButton()
            chooser.show()
            chooser.connect('selection-changed', self._on_changed)
            self.add(chooser)

    def get_filename(self):
        if os.name == 'nt':
            return self._entry.get_text()
        else:
            return self._filechooser.get_filename()

    def set_filename(self, filename):
        if os.name == 'nt':
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


class ValueChooser(gtk.ComboBox):

    __gtype_name__ = 'ValueChooser'

    gsignal('value-changed')

    def __init__(self, db, field):
        super(ValueChooser, self).__init__()
        self.db = db
        self.field = field
        self.model = gtk.ListStore(str, object)
        self.set_row_separator_func(self.is_row_separator)
        self._populate()
        self.set_model(self.model)
##         cell = self.cell_pb = gtk.CellRendererPixbuf()
##         self.pack_start(cell, False)
##         self.set_cell_data_func(cell, self.cell_icon)
        cell = self.cell_text = gtk.CellRendererText()
        self.pack_start(cell)
        self.add_attribute(cell, 'text', 0)
        self.select_item_by_data(field.get())
        self.connect('changed', self._on_changed)

##     def cell_icon(self, layout, cell, model, row):
##         entity = model[row][1]
##         if entity in (UNASSIGNED, None):
##             cell.set_property('stock_id', gtk.STOCK_NO)
##             cell.set_property('stock_size', gtk.ICON_SIZE_SMALL_TOOLBAR)
##             cell.set_property('visible', False)
##         else:
##             extent = entity.sys.extent
##             pixbuf = icon.small_pixbuf(self, extent)
##             cell.set_property('pixbuf', pixbuf)
##             cell.set_property('visible', True)

    def get_selected(self):
        iter = self.get_active_iter()
        if iter:
            return self.model[iter][1]

    def is_row_separator(self, model, row):
        text, entity = model[row]
        if text is None and entity is None:
            return True
        return False

    def select_item_by_data(self, data):
        for row in self.model:
            if row[1] == data:
                self.set_active_iter(row.iter)
                break

    def _on_changed(self, widget):
        self.emit('value-changed')

##     def _on_entry__activate(self, entry):
##         self.emit('activate')

##     def _on_entry__changed(self, entry):
##         self.emit('value-changed')

    def _populate(self):
        db = self.db
        field = self.field
        items = []
        values = []
        # Unassigned.
        items.append((u'<UNASSIGNED>', UNASSIGNED))
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

type_register(ValueChooser)


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
