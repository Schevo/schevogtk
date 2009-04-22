"""Database-level pygtk widgets."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import gtk
import gobject

from schevo import base
from schevo.gtk import icon
from schevo.label import label, plural


class ExtentExpanderBox(gtk.VBox):

    def __init__(self, db):
        gtk.VBox.__init__(self)
        self._db = db
##         exp_ext = self._expander_extent = {}
##         ext_exp = self._extent_expander = {}
        for extent in db.extents():
            expander = gtk.Expander()
            extent_label = plural(extent)
            iset = icon.iconset(self, extent)
            image_label = icon.small_image(self, extent)
##             text_label = gtk.Label(u'<b>%s</b>' % extent_label)
##             text_label.props.use_markup = True
            text_label = gtk.Label(extent_label)
            label_widget = gtk.HBox()
            label_widget.pack_start(image_label, expand=False, padding=6)
            label_widget.pack_start(text_label, expand=False)
            expander.props.label_widget = label_widget
            self.pack_start(expander)
            # Children of expander.
            hbox = gtk.HBox()
            expander.add(hbox)
            # Padding on left.
            padding = gtk.VBox()
            padding.props.width_request = 20
            hbox.pack_start(padding, expand=False)
            # Buttons.
            buttons = gtk.VBox()
            hbox.add(buttons)
            # Query buttons.
            q = extent.q
            for q_name in q:
                q_method = q[q_name]
##                 q_label = label(q_method)
                q_label = gtk.Label(label(q_method))
                q_button = gtk.Button()
##                 q_button.props.label = q_label
##                 q_button.props.image = icon.small_image(
##                     self, db, 'q.%s' % q_name)
                q_image = icon.small_image(self, db, 'q.%s' % q_name)
                q_hbox = gtk.HBox(spacing=2)
                q_hbox.pack_start(q_image, expand=False)
                q_hbox.pack_start(q_label, expand=False, padding=1)
                q_button.add(q_hbox)
##                 q_button.props.relief = gtk.RELIEF_NONE
                q_button.props.xalign = 0.0
                q_button.connect(
                    'clicked', self.on_q_button_clicked,
                    extent, q_name)
                buttons.add(q_button)
            # Transaction buttons.
            t = extent.t
            for t_name in t:
                t_method = t[t_name]
                t_label = label(t_method)
                t_button = gtk.Button()
                t_button.props.label = t_label
                t_button.props.image = icon.small_image(
                    self, db, 't.%s' % t_name)
##                 t_button.props.relief = gtk.RELIEF_NONE
                t_button.props.xalign = 0.0
                t_button.connect(
                    'clicked', self.on_t_button_clicked,
                    extent, t_name)
                buttons.add(t_button)
            # Padding on bottom.
            padding = gtk.VBox()
            padding.props.height_request = 11
            buttons.add(padding)
        self.show_all()

    def on_q_button_clicked(self, button, extent, method_name):
        self.emit('q_method_activated', extent, method_name)

    def on_t_button_clicked(self, button, extent, method_name):
        self.emit('t_method_activated', extent, method_name)

##     def expander_for(self, extent):
##         return self._extent_expander[extent]

##     def extent_for(self, expander):
##         return self._expander_extent[expander]


gobject.signal_new(
    'q_method_activated', ExtentExpanderBox, gobject.SIGNAL_RUN_LAST,
    gobject.TYPE_BOOLEAN, (gobject.TYPE_PYOBJECT, gobject.TYPE_STRING))

gobject.signal_new(
    't_method_activated', ExtentExpanderBox, gobject.SIGNAL_RUN_LAST,
    gobject.TYPE_BOOLEAN, (gobject.TYPE_PYOBJECT, gobject.TYPE_STRING))
