"""Grid widget.

For copyright, license, and warranty, see bottom of file.
"""

import gc
import sys
from schevo.lib import optimize

import gtk
from gtk import gdk
import gobject

from kiwi.ui import objectlist


WATCH = gdk.Cursor(gdk.WATCH)


class Column(objectlist.Column):

    get_attribute = getattr


class CallableColumn(Column):

    def get_attribute(self, model, attr_name, default=None):
        attr = getattr(model, attr_name)
        return attr()


class Grid(objectlist.ObjectList):

    def __init__(self, columns=[], instances=None, mode=gtk.SELECTION_BROWSE):
        self._bindings = {}
        self._filter = None
        self._row_popup_menu = None
        super(Grid, self).__init__(columns, instances, mode)
        self._treeview.connect('button-release-event',
                               self._on_treeview__button_release_event)
        self._treeview.connect_after('key-press-event',
                                     self._after_treeview__key_press_event)

    def set_cursor(self, cursor=None):
        window = self.window
        # Since a ScrolledWindow doesn't have an X window this window
        # will be the same as this widget's parent window.
        if window is not None:
            window.set_cursor(cursor)

    def set_rows(self, instances):
        self.set_cursor(WATCH)
        model = self._model
        view = self._treeview
        view.freeze_notify()
        view.set_model(None)
        self.unselect_all()
        self.clear()
        gc.collect()
##         model.set_sort_column_id(1, gtk.SORT_ASCENDING)
        if instances:
            iters = self._iters
            for instance in instances:
                inst_id = id(instance)
                iters[inst_id] = model.append((instance,))
            if self._autosize:
                view.columns_autosize()
                self._autosize = False
        if self._filter is not None:
            view.set_model(self._filter)
        else:
            view.set_model(model)
        view.thaw_notify()
        self.set_cursor()

    def _after_treeview__key_press_event(self, widget, event):
        keyval = event.keyval
        mask = event.state & gdk.MODIFIER_MASK
        binding = (keyval, mask)
        if binding in self._bindings:
            func = self._bindings[binding]
            func()

    def _on_treeview__button_release_event(self, treeview, event):
        if event.button == 3 and self._row_popup_menu is not None:
            instance = self.get_selected()
            self._row_popup_menu.popup(event, instance)


class PopupMenu(gtk.Menu):

    def __init__(self):
        self._instance = None
        self._signals = []
        super(PopupMenu, self).__init__()

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
            super(PopupMenu, self).popup(None, None, None,
                                         event.button, event.time)


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
