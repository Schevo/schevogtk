"""Database Window class.

For copyright, license, and warranty, see bottom of file.
"""

from __future__ import with_statement

import sys
from schevo.lib import optimize

import gtk
from gtk import gdk

import os

from schevo.constant import UNASSIGNED
import schevo.database
from schevo.introspect import isselectionmethod

from schevogtk2.cursor import TemporaryCursor
from schevogtk2 import dialog
from schevogtk2.error import FriendlyErrorDialog
from schevogtk2.field import (
    DEFAULT_GET_VALUE_HANDLERS, DEFAULT_SET_FIELD_HANDLERS)
from schevogtk2 import form
from schevogtk2 import icon
from schevogtk2.widgettree import GladeSignalBroker, WidgetTree


WATCH = gdk.Cursor(gdk.WATCH)


class BaseWindow(object):

    gladefile = ''

    get_value_handlers = DEFAULT_GET_VALUE_HANDLERS
    set_field_handlers = DEFAULT_SET_FIELD_HANDLERS

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
        self._statusbar_context = self.statusbar.get_context_id('APP')

    def after_tx(self, tx, tx_result):
        pass

    def before_tx(self, tx, action):
        pass

    def destroy(self, *args):
        self.toplevel.destroy()

    def get_focus(self):
        return self.toplevel.get_focus()

    def set_focus(self, widget):
        return self.toplevel.set_focus(widget)

    def status(self, text=None):
        statusbar = self.statusbar
        context = self._statusbar_context
        if text is None:
            statusbar.pop(context)
            while gtk.events_pending():
                gtk.main_iteration()
        else:
            statusbar.push(context, ' ' + text)
            while gtk.events_pending():
                gtk.main_iteration()
            return _StatusbarContextManager(statusbar, context)

    def get_title(self):
        return self.toplevel.get_title()

    def set_title(self, title):
        return self.toplevel.set_title(title)

    def message(self, text, title=None):
        flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        dialog = gtk.MessageDialog(parent=self.toplevel, flags=flags,
                                   buttons=gtk.BUTTONS_OK,
                                   message_format=text)
        if title is not None:
            dialog.set_title(title)
        dialog.run()
        dialog.destroy()

    def _on_action_selected(self, widget, action):
        if action.type == 'relationship':
            entity = action.instance
            self.run_relationship_dialog(entity)
        elif action.type == 'transaction':
            if not isselectionmethod(action.method):
                tx = action.method()
            else:
                tx = action.method(action.selection)
            if action.related is not None:
                # Initialize the related field if the transaction
                # setup hasn't already done so or set it to readonly.
                field_name = action.related.field_name
                if (field_name in tx.f and not tx.f[field_name].readonly and
                    getattr(tx, field_name) is UNASSIGNED):
                    setattr(tx, field_name, action.related.entity)
            self.before_tx(tx, action)
            tx_result = self.run_tx_dialog(tx, action)
            if tx.sys.executed:
                reflect_changes = getattr(widget, 'reflect_changes', None)
                if reflect_changes:
                    reflect_changes(tx_result, tx)
            self.reflect_changes(tx_result, tx)
            self.after_tx(tx, tx_result)
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
        with TemporaryCursor(self):
            db = self._db
            parent = self.toplevel
            dialog = relationship.RelationshipWindow(db, entity)
            dialog.after_tx = self.after_tx
            dialog.before_tx = self.before_tx
            # Be sure to set the get_value and set_field handlers to match
            # this window.
            dialog.get_value_handlers = self.get_value_handlers
            dialog.set_field_handlers = self.set_field_handlers
            window = dialog.toplevel
            window.set_modal(True)
            window.set_transient_for(parent)
            window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        dialog.run()
        dialog.destroy()

    def run_tx_dialog(self, tx, action):
        with TemporaryCursor(self):
            db = self._db
            parent = self.toplevel
            dialog = form.get_tx_dialog(
                parent, db, tx, action,
                self.get_value_handlers, self.set_field_handlers,
                )
        dialog.run()
        tx_result = dialog.tx_result
        dialog.destroy()
        return tx_result

    def run_view_dialog(self, entity, action):
        with TemporaryCursor(self):
            db = self._db
            parent = self.toplevel
            dialog = form.get_view_dialog(
                parent, db, entity, action,
                self.get_value_handlers, self.set_field_handlers,
                )
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

    file_location = '.'
    file_ext_patterns = ['*.db', '*.schevo']
    file_ext_patterns_description = 'Schevo Database Files'
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
            with TemporaryCursor(self):
                self._db.close()
                self._db = None
                self._db_filename = None
                self.update_ui()

    def database_new(self, filename):
        """Create a new database file."""
        raise NotImplementedError

    def database_open(self, filename):
        """Open a database file."""
        self.database_close()
        with TemporaryCursor(self):
            try:
                self._db = schevo.database.open(filename)
            except:
                msg = 'Unable to open %s' % filename
                self.message(msg)
            else:
                self._db_filename = filename
                self.update_ui()

    def database_pack(self):
        """Pack the currently open database file."""
        if self._db is not None:
            with TemporaryCursor(self):
                self._db.pack()

    def on_Close__activate(self, action):
        self.database_close()

    def on_New__activate(self, action):
        filename = dialog.save(
            title=self.file_new_title,
            parent=self.toplevel,
            patterns=self.file_ext_patterns,
            description=self.file_ext_patterns_description,
            folder=self.file_location,
            default_extension=self.file_new_default_extension,
            )
        if filename:
            self.database_new(filename)

    def on_Open__activate(self, action):
        filename = dialog.open(
            title=self.file_open_title,
            parent=self.toplevel,
            patterns=self.file_ext_patterns,
            description=self.file_ext_patterns_description,
            folder=self.file_location,
            )
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


class EmptyWindow(BaseWindow):

    # By default, quit the gtk main loop when hiding, since the most
    # common use for this class is for modal dialogs.
    quit_on_hide = True

    def hide(self):
        self.toplevel.hide()
        if self.quit_on_hide:
            self.quit()

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


class _StatusbarContextManager(object):

    def __init__(self, statusbar, context):
        self.statusbar = statusbar
        self.context = context

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.statusbar.pop(self.context)
        while gtk.events_pending():
            gtk.main_iteration()
        # Do not ignore exception.
        return False


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
