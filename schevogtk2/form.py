"""Form classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import gtk
from gtk import gdk

import schevo.base
from schevo.label import label

from schevogtk2.field import FieldLabel, DynamicField
from schevogtk2 import plugin
from schevogtk2.utils import gsignal


class FormBox(gtk.VBox):

    def __init__(self):
        super(FormBox, self).__init__()
        self.field_widgets = {}
        self.set_border_width(10)
        self.set_spacing(10)
        self.header = gtk.Label()
        self.pack_start(self.header, expand=False, fill=False, padding=0)
        self.header_sep = gtk.HSeparator()
        self.pack_start(self.header_sep, expand=False, fill=False, padding=0)
        self.table = None

    def set_fields(self, db, fields):
        field_count = len(fields)
        if field_count > 0:
            self.table = get_table(db, fields, self.field_widgets)
            self.table.show()
            self.pack_start(self.table, expand=True, fill=True, padding=0)

    def set_header_text(self, text):
        self.header.set_text(text)
        self.header.show()
        self.header_sep.show()


class FormWindow(gtk.Window):

    def __init__(self):
        super(FormWindow, self).__init__()
        self._bindings = {}
        self._db = None
        self._model = None
        self.tx_result = None
        self.vbox = vbox = gtk.VBox()
        vbox.set_spacing(5)
        vbox.set_border_width(5)
        self.set_default_size(400, -1)
        vbox.show()
        self.form_box = fbox = FormBox()
        fbox.show()
        self.footer_sep = fsep = gtk.HSeparator()
        fsep.show()
        self.button_box = bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_END)
        bbox.set_spacing(5)
        bbox.show()
        self.ok_button = button = gtk.Button(stock=gtk.STOCK_OK)
        button.connect('clicked', self.on_ok_button__clicked)
        self.button_box.add(button)
        self.cancel_button = button = gtk.Button(stock=gtk.STOCK_CANCEL)
        button.connect('clicked', self.on_cancel_button__clicked)
        self.button_box.add(button)
        self.close_button = button = gtk.Button(stock=gtk.STOCK_CLOSE)
        button.connect('clicked', self.on_close_button__clicked)
        self.button_box.add(button)
        vbox.pack_start(fbox, expand=True, fill=True, padding=0)
        vbox.pack_start(fsep, expand=False, fill=False, padding=0)
        vbox.pack_start(bbox, expand=False, fill=True, padding=0)
        self.add(vbox)
        self.connect('hide', self.quit)
        self.connect('key-press-event', self._on_key_press_event)
        self._set_bindings()

    def on_cancel_button__clicked(self, widget):
        self.hide()

    def on_close_button__clicked(self, widget):
        self.hide()

    def _on_key_press_event(self, window, event):
        keyval = event.keyval
        mask = event.state & gdk.MODIFIER_MASK
        binding = (keyval, mask)
        if binding in self._bindings:
            func = self._bindings[binding]
            func()

    def on_ok_button__clicked(self, widget):
        tx = self._model
        for name, widget in self.form_box.field_widgets.items():
            field = tx.f[name]
            if field.readonly:
                continue
            value = widget.get_value()
            try:
                setattr(tx, name, value)
            except Exception, e:
                show_error(self, Exception, e)
                return
        try:
            self.tx_result = self._db.execute(tx)
        except Exception, e:
            show_error(self, Exception, e)
            if not hasattr(sys, 'frozen'):
                raise
        except:
            raise
        else:
            self.hide()

    def quit(self, *args):
        gtk.main_quit()

    def run(self):
        self.show()
        gtk.main()

    def _set_bindings(self):
        items = [
            ('<Control>F4', self.hide),
            ('Escape', self.hide),
            ]
        self._bindings = dict([(gtk.accelerator_parse(name), func)
                               for name, func in items])
        # Hack to support these with CapsLock on.
        for name, func in items:
            keyval, mod = gtk.accelerator_parse(name)
            mod = mod | gtk.gdk.LOCK_MASK
            self._bindings[(keyval, mod)] = func

    def set_db(self, db):
        self._db = db

    def set_header_text(self, text):
        self.form_box.set_header_text(text)

    def set_fields(self, model, fields):
        self._model = model
        self.form_box.set_fields(self._db, fields)
        if isinstance(model, schevo.base.Transaction):
            self.ok_button.show()
            self.cancel_button.show()
            self.close_button.hide()
        else:
            self.ok_button.hide()
            self.cancel_button.hide()
            self.close_button.show()


def get_custom_tx_dialog(WindowClass, parent, db, tx):
    dialog = WindowClass(db, tx)
    window = dialog.toplevel
    window.set_modal(True)
    window.set_transient_for(parent)
    window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    return dialog

def get_default_tx_dialog(parent, db, tx):
    extent_name = tx.sys.extent_name
    if extent_name is None:
        title = u'%s' % label(tx)
        text = u'%s' % label(tx)
    else:
        title = u'%s :: %s' % (label(tx), extent_name)
        text = u'%s :: %s' % (label(tx), extent_name)
    field_map = tx.sys.field_map()
    fields = field_map.values()
    fields = [field for field in fields if not field.hidden]
    dialog = get_dialog(title, parent, text, db, tx, fields)
    return dialog

def get_dialog(title, parent, text, db, model, fields):
    window = FormWindow()
    window.set_db(db)
    window.set_modal(True)
    window.set_transient_for(parent)
    window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    window.set_title(title)
    window.set_header_text(text)
    fields = [field for field in fields if not field.hidden]
    window.set_fields(model, fields)
    return window

def get_table(db, fields, field_widgets):
    """Return a gtk.Table widget containing labels and dynamic field widgets
    for each field given.
    
    - `db`: The database containing the fields.
    
    - `fields`: Sequence of Schevo field instances to create widgets for.
    
    - `field_widgets`: Dictionary that is updated to store
      field-name:field-widget pairs as the field widgets are created.
    """
    field_count = len(fields)
    table = gtk.Table(rows=field_count, columns=2)
    table.set_row_spacings(5)
    table.set_col_spacings(5)
    row = 0
    for field in fields:
        # Skip hidden fields.
        if field.hidden:
            continue
        # Label.
        label_box = FieldLabel()
        label_box.set_field(db, field)
        label_box.show()
        # Widget.
        widget_box = DynamicField()
        widget_box.set_field(db, field)
        widget_box.show()
        # Attach to table.
        xoptions = gtk.FILL
        yoptions = gtk.FILL
        table.attach(label_box, 0, 1, row, row+1, xoptions, yoptions)
        xoptions = gtk.EXPAND|gtk.FILL
        yoptions = gtk.FILL
        if widget_box.expand:
            yoptions = gtk.EXPAND|gtk.FILL
        table.attach(widget_box, 1, 2, row, row+1, xoptions, yoptions)
        field_widgets[field.name] = widget_box
        row += 1
    return table

def get_tx_dialog(parent, db, tx, action):
    WindowClass = plugin.get_custom_tx_dialog_class(db, action)
    if WindowClass is None:
        dialog = get_default_tx_dialog(parent, db, tx)
    else:
        dialog = get_custom_tx_dialog(WindowClass, parent, db, tx)
    return dialog

def get_view_dialog(parent, db, entity, action):
    extent_text = label(entity.sys.extent)
    title = u'View :: %s' % (extent_text, )
    text = u'View :: %s :: %s' % (extent_text, entity)
    def include(field):
        if action.include_expensive:
            return True
        elif field.expensive:
            return False
        else:
            return True
    f_map = entity.sys.field_map(include)
    fields = f_map.values()
    dialog = get_dialog(title, parent, text, db, entity, fields)
    return dialog

def show_error(parent, exception, e):
    flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
    win = gtk.MessageDialog(parent=parent, flags=flags,
                            type=gtk.MESSAGE_ERROR,
                            buttons=gtk.BUTTONS_CLOSE,
                            message_format=str(e))
##     title = 'Error: %s' % (exception, )
##     win.set_title(title)
    win.run()
    win.destroy()


##         scrolled_window = gtk.ScrolledWindow()
##         scrolled_window.show()
##         vbox = gtk.VBox(spacing=4)
##         vbox.set_border_width(4)
##         vbox.show()
##         table = gtk.Table(rows=3, columns=2, homogeneous=False)
##         table.show()
##         vbox.pack_start(table, expand=False, fill=True, padding=0)
##         viewport = gtk.Viewport()
##         viewport.show()
##         viewport.set_shadow_type(gtk.SHADOW_NONE)
##         viewport.add(vbox)
##         scrolled_window.add(viewport)


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
