"""Schevo dynamic field widget.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from xml.sax.saxutils import escape
import os

import gobject
import gtk
import pango

import schevo.field
from schevo.label import label
from schevo.base import Entity, Transaction
from schevo.constant import UNASSIGNED

from schevogtk2 import fieldwidget
from schevogtk2.utils import gsignal, type_register


MONO_FONT = pango.FontDescription('monospace normal')


class DynamicField(gtk.HBox):

    __gtype_name__ = 'DynamicField'

    gsignal('create-clicked', object)
    gsignal('update-clicked', object)
    gsignal('view-clicked', object)
    gsignal('value-changed')

    def __init__(self, get_value_handlers, set_field_handlers):
        super(DynamicField, self).__init__()
        self.props.spacing = 5
        # Create the units label, hidden by default, packed to the end.
        units_label = self._units_label = gtk.Label()
        units_label.hide()
        self.pack_end(units_label, expand=False)
        # Begin as a single-line text entry field, until later changed
        # to another widget type.
        widget = gtk.Entry()
        widget.show()
        self.pack_start(widget)
        self.child = widget
        self._db = None
        self._field = None
        self.expand = False
        self.get_value_handlers = get_value_handlers
        self.set_field_handlers = set_field_handlers

    def get_value(self):
        widget = self.child
        for handler in self.get_value_handlers:
            widget, cont, value = handler(widget)
            if not cont:
                return value
        # We couldn't find an endpoint handler.
        raise ValueError(
            'Could not find an endpoint get_value handler for %r' % self.child)

    def reset(self):
        self.set_field(self._db, self._field)

    def set_field(self, db, field):
        self._db = db
        self._field = field
        if self.child is not None:
            self.remove(self.child)
        if field.hidden:
            # Do nothing for hidden fields.
            return
        control = None
        value = field.get()
        change_cb = self._on_widget__value_changed
        for handler in self.set_field_handlers:
            cont, widget, control = handler(self, db, field, value, change_cb)
            if not cont:
                if control is None:
                    control = widget
                if field.fget or field.readonly:
                    if hasattr(control.props, 'editable'):
                        control.props.editable = False
                        # Make it appear insensitive even though it's
                        # just read-only.
                        style = control.get_style()
                        insensitive_bg = style.bg[gtk.STATE_INSENSITIVE]
                        control.modify_base(gtk.STATE_NORMAL, insensitive_bg)
                    if hasattr(control.props, 'can-focus'):
                        control.props.can_focus = False
                    if hasattr(control.props, 'has-focus'):
                        control.props.has_focus = False
#                     if hasattr(control, 'set_selectable'):  # Label only.
#                         control.set_selectable(True)
                signal_names = gobject.signal_list_names(control.__class__)
                if 'create-clicked' in signal_names:
                    control.connect(
                        'create-clicked', self._on_widget__create_clicked)
                if 'update-clicked' in signal_names:
                    control.connect(
                        'update-clicked', self._on_widget__update_clicked)
                if 'view-clicked' in signal_names:
                    control.connect(
                        'view-clicked', self._on_widget__view_clicked)
                widget.show()
                self.pack_start(widget)
                self.child = widget
                # Hide or show units label as appropriate.
                if field.units:
                    self._units_label.show()
                    self._units_label.set_text(field.units)
                else:
                    self._units_label.hide()
                return
        # We couldn't find an endpoint handler.
        raise ValueError(
            'Could not find an endpoint set_field handler for %r' % self.child)

    def _on_widget__create_clicked(self, widget, allowed_extents):
        self.emit('create-clicked', allowed_extents)

    def _on_widget__update_clicked(self, widget, entity_to_update):
        self.emit('update-clicked', entity_to_update)

    def _on_widget__value_changed(self, widget, field):
        value = self.get_value()
##         print '%s changed to: %s %r:' % (field.name, value, value)
        self.emit('value-changed')

    def _on_widget__view_clicked(self, widget, entity_to_view):
        self.emit('view-clicked', entity_to_view)

type_register(DynamicField)


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


# get_value handlers accept the following positional arguments:
#
#   widget: The widget to get the value from.
#
# get_value handlers return a tuple:
#   (
#     widget, - The current widget we're working with to retrieve a value.
#     cont,   - True if we should continue in the chain, or False to stop.
#     value,  - The value retrieved from the widget, or None if continuing.
#   )

# All handlers are decorated with `optimize.do_not_optimize` since we
# need to determine where they are in the `DEFAULT_...` lists in order
# to insert custom handlers into custom handler lists.

@optimize.do_not_optimize
def _get_value_ScrolledWindow(widget):
    if isinstance(widget, gtk.ScrolledWindow):
        # Use the child widget if inspecting a scrolled window.
        widget = widget.child
    # Always continue.
    return (widget, True, None)

@optimize.do_not_optimize
def _get_value_CheckButton(widget):
    if isinstance(widget, gtk.CheckButton):
        value = widget.get_active()
        return (widget, False, value)
    else:
        return (widget, True, None)

@optimize.do_not_optimize
def _get_value_FileChooser(widget):
    if isinstance(widget, fieldwidget.FileChooser):
        value = widget.get_filename()
        return (widget, False, value)
    else:
        return (widget, True, None)

@optimize.do_not_optimize
def _get_value_Image(widget):
    if isinstance(widget, gtk.Image):
        # XXX: Hack since images cannot be edited.
        value = self._field.get()
        return (widget, False, value)
    else:
        return (widget, True, None)

@optimize.do_not_optimize
def _get_value_EntityChooser(widget):
    if isinstance(widget, fieldwidget.EntityChooser):
        value = widget.get_selected()
        if value is None:
            value = UNASSIGNED
        return (widget, False, value)
    else:
        return (widget, True, None)

@optimize.do_not_optimize
def _get_value_TextView(widget):
    if isinstance(widget, gtk.TextView):
        text_buffer = widget.props.buffer
        startiter, enditer = text_buffer.get_bounds()
        value = text_buffer.get_text(startiter, enditer)
        if not value:
            value = UNASSIGNED
        return (widget, False, value)
    else:
        return (widget, True, None)

@optimize.do_not_optimize
def _get_value_ValueChooser(widget):
    if isinstance(widget, fieldwidget.ValueChooser):
        value = widget.get_selected()
        if value is None:
            value = UNASSIGNED
        return (widget, False, value)
    else:
        return (widget, True, None)

@optimize.do_not_optimize
def _get_value_generic(widget):
    value = widget.get_text()
    if not value:
        value = UNASSIGNED
    return (widget, False, value)

DEFAULT_GET_VALUE_HANDLERS = [
    _get_value_ScrolledWindow,
    _get_value_CheckButton,
    _get_value_FileChooser,
    _get_value_Image,
    _get_value_EntityChooser,
    _get_value_TextView,
    _get_value_ValueChooser,
    _get_value_generic,
    ]


# set_value handlers accept the following positional arguments:
#
#   container: The widget that will eventually contain the field widget.
#   db:        The database the field is attached to.
#   field:     The field to create a widget for.
#   value:     The value of the field.
#   change_cb: Callback to call when the widget's value changes.
#
# set_value handlers return a tuple:
#   (
#     cont,    - True if we should continue in the chain, or False to stop.
#     widget,  - The new widget to attach to the DynamicField widget, or None.
#     control, - The control that handles user input; None if same as widget.
#   )

# All handlers are decorated with `optimize.do_not_optimize` since we
# need to determine where they are in the `DEFAULT_...` lists in order
# to insert custom handlers into custom handler lists.

@optimize.do_not_optimize
def _set_field_rw_boolean(container, db, field, value, change_cb):
    if isinstance(field, schevo.field.Boolean) and not field.readonly:
        widget = gtk.CheckButton()
        if value is UNASSIGNED:
            value = False
        widget.set_active(value)
        widget.set_label(unicode(value))
        def on_toggled(widget):
            widget.set_label(unicode(widget.get_active()))
        widget.connect('toggled', on_toggled)
        widget.connect('toggled', change_cb, field)
        return (False, widget, None)
    else:
        return (True, None, None)

@optimize.do_not_optimize
def _set_field_rw_entity(container, db, field, value, change_cb):
    if isinstance(field, schevo.field.Entity) and not field.readonly:
        widget = fieldwidget.EntityChooser(db, field)
        widget.connect('value-changed', change_cb, field)
        return (False, widget, None)
    else:
        return (True, None, None)

@optimize.do_not_optimize
def _set_field_image(container, db, field, value, change_cb):
    if isinstance(field, schevo.field.Image):
        widget = gtk.Image()
        if value is not UNASSIGNED:
            loader = gtk.gdk.PixbufLoader()
            loader.write(value)
            loader.close()
            pixbuf = loader.get_pixbuf()
            widget.set_from_pixbuf(pixbuf)
        return (False, widget, None)
    else:
        return (True, None, None)

@optimize.do_not_optimize
def _set_field_multiline_string(container, db, field, value, change_cb):
    if isinstance(field, schevo.field.String) and field.multiline:
        container.expand = True
        if value is UNASSIGNED:
            value = ''
        else:
            value = unicode(value)
        widget = gtk.ScrolledWindow()
        widget.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        widget.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        textview = gtk.TextView()
        if field.monospace:
            textview.modify_font(MONO_FONT)
        textview.set_accepts_tab(False)
        textview.show()
        textview.set_size_request(-1, 150)
        textbuff = textview.props.buffer
        textbuff.set_text(value)
#         textbuff.connect('changed', change_cb, field)
        widget.add(textview)
        return (False, widget, textview)
    else:
        return (True, None, None)

@optimize.do_not_optimize
def _set_field_calculated(container, db, field, value, change_cb):
    if field.fget:
        if value is UNASSIGNED:
            value = ''
        else:
            value = unicode(value)
        widget = gtk.Entry()
        widget.set_text(value)
        return (False, widget, None)
    else:
        return (True, None, None)

@optimize.do_not_optimize
def _set_field_rw_path(container, db, field, value, change_cb):
    if isinstance(field, schevo.field.Path) and not field.readonly:
        widget = fieldwidget.FileChooser(db, field)
        if value:
            widget.set_filename(value)
        widget.connect('value-changed', change_cb, field)
        return (False, widget, None)
    else:
        return (True, None, None)

@optimize.do_not_optimize
def _set_field_generic_valid_values(container, db, field, value, change_cb):
    if field.valid_values is not None and not (field.readonly or field.fget):
        widget = fieldwidget.ValueChooser(db, field)
        widget.connect('value-changed', change_cb, field)
        return (False, widget, None)
    else:
        return (True, None, None)

@optimize.do_not_optimize
def _set_field_generic(container, db, field, value, change_cb):
    if value is UNASSIGNED:
        value = ''
    else:
        value = unicode(value)
    widget = gtk.Entry()
    widget.set_text(value)
    widget.connect('activate', change_cb, field)
    widget.connect('changed', change_cb, field)
    return (False, widget, None)

DEFAULT_SET_FIELD_HANDLERS = [
    _set_field_rw_boolean,
    _set_field_rw_entity,
    _set_field_image,
    _set_field_multiline_string,
    _set_field_calculated,
    _set_field_rw_path,
    _set_field_generic_valid_values,
    _set_field_generic,
    ]


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
