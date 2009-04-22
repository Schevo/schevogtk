"""Schevo+GTK Navigator app widget."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import gtk

from schevo.gtk.database import ExtentExpanderBox
from schevo.gtk.query import Query
from schevo.gtk.transaction import Transaction
from schevo.gtk.widget import BrowserStack
from schevo.label import plural


class AppWidget(gtk.HPaned):

    def __init__(self, db):
        super(AppWidget, self).__init__()
        self._db = db
        # Create extent list.
        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        container = gtk.VBox()
        scroller.add_with_viewport(container)
        expanders = self._extent_expanders = ExtentExpanderBox(db)
        expanders.connect(
            'q_method_activated', self.on_extent_q_method_activated)
        expanders.connect(
            't_method_activated', self.on_extent_t_method_activated)
        container.pack_start(expanders, expand=False)
##         container.pack_start(gtk.VBox(), expand=True)
        self.pack1(scroller, resize=False, shrink=False)
        # Create browser stack.
        stack = self._stack = BrowserStack()
        self.pack2(stack, resize=True, shrink=False)
        self.show_all()

    def on_extent_q_method_activated(self, widget, extent, method_name):
        page = Query(self._db, extent, method_name)
        self._stack.browse_to(page)

    def on_extent_t_method_activated(self, widget, extent, method_name):
        page = Transaction(self._db, extent, method_name)
        self._stack.browse_to(page)
