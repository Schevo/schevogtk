"""Schevo field widgets.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import gtk

import schevo.field
from schevo.label import label
from schevo.constant import UNASSIGNED

from kiwi.ui.widgets.combo import ProxyComboEntry
## from kiwi.ui.widgets.checkbutton import ProxyCheckButton
## from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.label import ProxyLabel

from kiwi.utils import gsignal, type_register


HIGHLIGHT_COLOR_NAME = 'LightSteelBlue'
HIGHLIGHT_COLOR = gtk.gdk.color_parse(HIGHLIGHT_COLOR_NAME)


class FieldLabel(gtk.EventBox):

    __gtype_name__ = 'FieldLabel'

    def __init__(self):
        super(FieldLabel, self).__init__()
        text = u'Field label:'
        label = ProxyLabel()
        label.set_text(text)
        label.set_alignment(1.0, 0.5)
        label.set_bold(True)
        label.set_padding(5, 0)
        label.show()
        self.add(label)

    def set_field(self, db, field):
        label = self.child
        text = u'%s:' % (field.label)
        label.set_text(text)
        if field.readonly:
            label.set_bold(False)
        else:
            label.set_bold(True)
        if not field.required and not field.readonly:
            self.modify_bg(gtk.STATE_NORMAL, HIGHLIGHT_COLOR)

type_register(FieldLabel)


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
        elif isinstance(widget, gtk.FileChooserButton):
            value = widget.get_filename()
        elif isinstance(widget, ProxyComboEntry):
            value = widget.get_selected()
            if value is None:
                value = UNASSIGNED
        elif isinstance(widget, gtk.TextView):
            text_buffer = widget.props.buffer
            startiter, enditer = text_buffer.get_bounds()
            value = text_buffer.get_text(startiter, enditer)
            if not value:
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
        # Boolean.
        if isinstance(field, schevo.field.Boolean) and not field.readonly:
            widget = gtk.CheckButton()
            widget.set_active(value)
            widget.set_label(unicode(value))
            def on_toggled(widget):
                widget.set_label(unicode(widget.get_active()))
            widget.connect('toggled', on_toggled)
            widget.connect('toggled', self._on_widget__value_changed, field)
        # Entity.
        elif isinstance(field, schevo.field.Entity) and not field.readonly:
            allow = field.allow
            if len(allow) > 1:
                allow_multiple = True
            else:
                allow_multiple = False
            widget = ProxyComboEntry()
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
                for entity in preferred_values:
                    extent_text = label(entity.sys.extent)
                    if allow_multiple:
                        text = u'%s :: %s' % (entity, extent_text)
                    else:
                        text = u'%s' % (entity, )
                    more.append((text, entity))
                more.sort()
                items.extend(more)
                # Empty row separator.
                items.append(('-' * 20, None))
            more = []
            valid_values = field.valid_values
            if valid_values is not None:
                # Specific valid values.
                values.extend(valid_values)
                for entity in valid_values:
                    extent_text = label(entity.sys.extent)
                    if entity in preferred_values:
                        continue
                    if allow_multiple:
                        text = u'%s :: %s' % (entity, extent_text)
                    else:
                        text = u'%s' % (entity, )
                    more.append((text, entity))
            else:
                # Other allowed values.
                for extent_name in field.allow:
                    extent = db.extent(extent_name)
                    extent_text = label(extent)
                    for entity in extent.find():
                        if entity in preferred_values:
                            continue
                        values.append(entity)
                        if allow_multiple:
                            text = u'%s :: %s' % (entity, extent_text)
                        else:
                            text = u'%s' % (entity, )
                        more.append((text, entity))
            more.sort()
            items.extend(more)
            if value not in values:
                entity = value
                extent_text = label(entity.sys.extent)
                # Empty row separator.
                items.append(('=' * 20, None))
                if allow_multiple:
                    text = u'%s :: %s' % (entity, extent_text)
                else:
                    text = u'%s' % (entity, )
                items.append((text, entity))
            widget.prefill(items)
            widget.select_item_by_data(value)
            widget.connect('content-changed',
                           self._on_widget__value_changed, field)
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
            textview.show()
            textview.set_size_request(-1, 150)
            textbuff = textview.props.buffer
            textbuff.set_text(value)
##             textbuff.connect('changed', self._on_widget__value_changed, field)
            widget.add(textview)
        # Path.
        elif isinstance(field, schevo.field.Path) and not field.readonly:
            title = u'Select a file'
            widget = gtk.FileChooserButton(title)
            if field.file_only:
                widget.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
            elif field.directory_only:
                widget.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
            if value:
                widget.set_filename(value)
            widget.connect('selection-changed',
                           self._on_widget__value_changed, field)
        # All other field types.
        else:
            if value is UNASSIGNED:
                value = ''
            else:
                value = unicode(value)
            widget = gtk.Entry()
            widget.set_text(value)
            widget.connect('activate', self._on_widget__value_changed, field)
##         data_type = field.data_type
##         widget.set_property('data-type', data_type)
##         widget.set_property('model_attribute', field.name)
        if control is None:
            control = widget
        if field.readonly:
            control.set_editable(False)
##             control.set_sensitive(False)
        widget.show()
        self.add(widget)

    def _on_widget__value_changed(self, widget, field):
        value = self.get_value()
##         print '%s changed to: %s %r:' % (field.name, value, value)
        self.emit('value-changed')

type_register(DynamicField)


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
