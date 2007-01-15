"""Database Window class.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import gtk
from gtk import gdk

import os

if os.name == 'nt':
    import pywintypes
    import win32con
    import win32gui

import schevo.database
from schevo.constant import UNASSIGNED

from schevogtk2 import dialog
from schevogtk2 import form
from schevogtk2 import icon
from schevogtk2.widgettree import GladeSignalBroker, WidgetTree


WATCH = gdk.Cursor(gdk.WATCH)


class BaseWindow(object):

    gladefile = ''
    
    def __init__(self):
        self._bindings = {}
        self._db = None
        self.widgets = []
        wt = self._glade_adaptor = WidgetTree(self, self.gladefile,
                                              self.widgets)
        toplevel = self.toplevel = wt.get_widget(self.gladefile)
        assert isinstance(toplevel, gtk.Window)
        toplevel.connect('delete-event', self._on_delete_event)
        toplevel.connect('key-press-event', self._on_key_press_event)
        self._accel_groups = gtk.accel_groups_from_object(toplevel)
        self._broker = GladeSignalBroker(self, self)
        self._set_bindings()

    def after_tx(self, tx):
        pass

    def before_tx(self, tx):
        pass

    def destroy(self, *args):
        self.toplevel.destroy()

    def get_focus(self):
        return self.toplevel.get_focus()

    def set_focus(self, widget):
        return self.toplevel.set_focus(widget)

    def get_title(self):
        return self.toplevel.get_title()

    def set_title(self, title):
        return self.toplevel.set_title(title)

    def message(self, text):
        flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        dialog = gtk.MessageDialog(parent=self.toplevel, flags=flags,
                                   buttons=gtk.BUTTONS_OK,
                                   message_format=text)
        dialog.run()
        dialog.destroy()

    def _on_action_selected(self, widget, action):
        if action.type == 'relationship':
            entity = action.instance
            self.run_relationship_dialog(entity)
        elif action.type == 'transaction':
            tx = action.method()
            if action.related is not None:
                # Initialize the related field if the transaction
                # setup hasn't already done so or set it to readonly.
                field_name = action.related.field_name
                if (field_name in tx.f and not tx.f[field_name].readonly and
                    getattr(tx, field_name) is UNASSIGNED):
                    setattr(tx, field_name, action.related.entity)
            self.before_tx(tx)
            tx_result = self.run_tx_dialog(tx, action)
            if tx.sys.executed:
                widget.reflect_changes(tx_result, tx)
                self.reflect_changes(tx_result, tx)
            self.after_tx(tx)
        elif action.type == 'view':
            entity = action.instance
            self.run_view_dialog(entity, action)
        # XXX Hack due to a bug where this window doesn't become
        # active when one modal dialog leads to another (including the
        # dialog used by FileChooserButton, or an error message).
        self.toplevel.present()

    def _on_delete_event(self, window, event):
        self.quit()

    def _on_grid__row_activated(self, widget, entity):
        widget.select_view_action()

    def _on_key_press_event(self, window, event):
        keyval = event.keyval
        mask = event.state & gdk.MODIFIER_MASK
        binding = (keyval, mask)
        if binding in self._bindings:
            func = self._bindings[binding]
            func()

    def quit(self, *args):
        gtk.main_quit()

    def reflect_changes(self, result, tx):
        pass

    def run(self):
        self.show()
        gtk.main()

    def run_relationship_dialog(self, entity):
        from schevogtk2 import relationship
        self.set_cursor(WATCH)
        db = self._db
        parent = self.toplevel
        dialog = relationship.RelationshipWindow(db, entity)
        window = dialog.toplevel
        window.set_modal(True)
        window.set_transient_for(parent)
        window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_cursor()
        dialog.run()
        dialog.destroy()

    def run_tx_dialog(self, tx, action):
        self.set_cursor(WATCH)
        db = self._db
        parent = self.toplevel
        dialog = form.get_tx_dialog(parent, db, tx, action)
        self.set_cursor()
        dialog.run()
        tx_result = dialog.tx_result
        dialog.destroy()
        return tx_result

    def run_view_dialog(self, entity, action):
        self.set_cursor(WATCH)
        db = self._db
        parent = self.toplevel
        dialog = form.get_view_dialog(parent, db, entity, action)
        self.set_cursor()
        dialog.run()
        dialog.destroy()

    def _set_bindings(self):
        items = [
            ('<Control>F4', self.database_close),
            ]
        self._bindings = dict([(gtk.accelerator_parse(name), func)
                               for name, func in items])
        # Hack to support these with CapsLock on.
        for name, func in items:
            keyval, mod = gtk.accelerator_parse(name)
            mod = mod | gtk.gdk.LOCK_MASK
            self._bindings[(keyval, mod)] = func

    def set_cursor(self, cursor=None):
        window = self.toplevel.window
        # If the app isn't running yet there is no gdk.window.
        if window is not None:
            window.set_cursor(cursor)

    def show(self):
        self.toplevel.show()

    def _get_all_methods(self, klass=None):
        klass = klass or self.__class__
        # Very poor simulation of inheritance.
        classes = [klass]
        # Collect bases for class, using recursion.
        for klass in classes:
            map(classes.append, klass.__bases__)
        # Order bases so that the class itself is the last one
        # referred to in the loop. This guarantees that the
        # inheritance ordering for the methods is preserved.
        classes.reverse()
        methods = {}
        for c in classes:
            for name in c.__dict__.keys():
                # Use getattr() to ensure we get bound methods.
                methods[name] = getattr(self, name)
        return methods


class Window(BaseWindow):

    if os.name == 'nt':
        file_location = '.'
        file_ext_filter = 'Schevo Database Files\0*.db;*.schevo\0'
        file_custom_filter = 'All Files\0*.*\0'
        file_new_default_extension = 'db'
        file_new_title = 'New Schevo Database File'
        file_open_title = 'Open Schevo Database File'

    def __init__(self):
        BaseWindow.__init__(self)
        self._db_filename = None

    def create_backup(self, filename):
        if os.path.isfile(filename):
            n = 1
            backup_filename = filename + '.bk%s' % n
            while os.path.isfile(backup_filename):
                n += 1
                backup_filename = filename + '.bk%s' % n
            os.rename(filename, backup_filename)
            # Popup a message telling them the file was renamed.
            msg = '%s already exists, so a backup copy was saved as %s.' % (
                filename, backup_filename)
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
            dialog = gtk.MessageDialog(parent=self.toplevel, flags=flags,
                                       buttons=gtk.BUTTONS_OK,
                                       message_format=msg)
            dialog.run()
            dialog.destroy()

    def database_close(self):
        """Close an existing database file."""
        if self._db is not None:
            self.set_cursor(WATCH)
            self._db.close()
            self._db = None
            self._db_filename = None
            self.update_ui()
            self.set_cursor()

    def database_new(self, filename):
        """Create a new database file."""
        raise NotImplementedError
    
    def database_open(self, filename):
        """Open a database file."""
        self.database_close()
        self.set_cursor(WATCH)
        label = os.path.basename(filename)
        try:
            self._db = schevo.database.open(filename, label=label)
        except:
            msg = 'Unable to open %s' % filename
            self.message(msg)
        else:
            self._db_filename = filename
            self.update_ui()
        self.set_cursor()

    def database_pack(self):
        """Pack the currently open database file."""
        if self._db is not None:
            self.set_cursor(WATCH)
            self._db.pack()
            self.set_cursor()

    def on_Close__activate(self, action):
        self.database_close()

    def on_New__activate(self, action):
        filename = None
        if os.name == 'nt':
            try:
                filename, custom_filter, flags = win32gui.GetSaveFileNameW(
                    InitialDir=self.file_location,
                    Flags=win32con.OFN_EXPLORER|win32con.OFN_OVERWRITEPROMPT,
                    File='',
                    DefExt=self.file_new_default_extension,
                    Title=self.file_new_title,
                    Filter=self.file_ext_filter,
                    CustomFilter=self.file_custom_filter,
                    FilterIndex=1)
            except pywintypes.error:
                # Cancel button raises an exception.
                pass
##         else:
##             filename = dialog.open(title='Select a database file to open',
##                                    parent=self.toplevel,
##                                    patterns=['*.db', '*.schevo', '*.*'])
        if filename:
            self.database_new(filename)

    def on_Open__activate(self, action):
        filename = None
        if os.name == 'nt':
            try:
                filename, custom_filter, flags = win32gui.GetOpenFileNameW(
                    InitialDir=self.file_location,
                    Flags=win32con.OFN_EXPLORER|win32con.OFN_FILEMUSTEXIST,
                    File='',
                    DefExt='',
                    Title=self.file_open_title,
                    Filter=self.file_ext_filter,
                    CustomFilter=self.file_custom_filter,
                    FilterIndex=1)
            except pywintypes.error:
                # Cancel button raises an exception.
                pass
        else:
            filename = dialog.open(title='Select a database file to open',
                                   parent=self.toplevel,
                                   patterns=['*.db', '*.schevo', '*.*'])
        if filename:
            self.database_open(filename)

    def on_Quit__activate(self, action):
        self.quit()

    def run(self):
        self.show()
        gtk.main()

    def _set_bindings(self):
        items = [
            ('<Control>F4', self.database_close),
            ]
        self._bindings = dict([(gtk.accelerator_parse(name), func)
                               for name, func in items])
        # Hack to support these with CapsLock on.
        for name, func in items:
            keyval, mod = gtk.accelerator_parse(name)
            mod = mod | gtk.gdk.LOCK_MASK
            self._bindings[(keyval, mod)] = func

    def show_and_loop(self):
        self.show()
        gtk.main()

    def update_ui(self):
        """Update the interface to reflect the state of the database."""
        pass

    def _get_all_methods(self, klass=None):
        klass = klass or self.__class__
        # Very poor simulation of inheritance.
        classes = [klass]
        # Collect bases for class, using recursion.
        for klass in classes:
            map(classes.append, klass.__bases__)
        # Order bases so that the class itself is the last one
        # referred to in the loop. This guarantees that the
        # inheritance ordering for the methods is preserved.
        classes.reverse()
        methods = {}
        for c in classes:
            for name in c.__dict__.keys():
                # Use getattr() to ensure we get bound methods.
                methods[name] = getattr(self, name)
        return methods


class CustomWindow(BaseWindow):

    def __init__(self, db, tx):
        BaseWindow.__init__(self)
        self._db = db
        self._tx = tx
        self.tx_result = None
        self.toplevel.connect('hide', self.quit)
        self._set_widgets()

    def execute_tx(self):
        tx = self._tx
        for name in tx.f:
            field = tx.f[name]
            if field.readonly:
                continue
            widget = getattr(self, name)
            value = widget.get_value()
            try:
                setattr(tx, name, value)
            except Exception, e:
                show_error(self.toplevel, Exception, e)
                return
        try:
            self.result = self._db.execute(tx)
        except Exception, e:
            show_error(self.toplevel, Exception, e)
            if not hasattr(sys, 'frozen'):
                raise
        except:
            raise
        else:
            self.hide()

    def hide(self):
        self.toplevel.hide()

    def run(self):
        self.toplevel.show()
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

    def _set_widgets(self):
        db = self._db
        tx = self._tx
        for name in tx.f:
            field = tx.f[name]
            # Skip hidden fields.
            if field.hidden:
                continue
            label = getattr(self, name + '__label')
            label.set_field(db, field)
            widget = getattr(self, name)
            widget.set_field(db, field)


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
