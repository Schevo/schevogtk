"""Schevo+GTK query widget.

For copyright, license, and warranty, see bottom of file.
"""

from dispatch import generic

from schevo import base
from schevo import fieldspec
from schevo.gtk import icon
from schevo.gtk import field as gtk_field
from schevo.gtk import widget
from schevo.label import label, plural
from schevo import query as Q

import gobject
import gtk

from kiwi.ui.objectlist import ObjectList, Column


class Query(gtk.VBox):

    def __init__(self, db, extent, method_name):
        super(Query, self).__init__()
        self._db = db
        self._extent = extent
        method = extent.q[method_name]
        query = self._query = method()
        # Criteria form.
        expander_label = gtk.HBox()
        image_label = icon.small_image(self, db, 'q.%s' % method_name)
        text_label = gtk.Label(label(method))
        expander_label.pack_start(image_label, expand=False, padding=6)
        expander_label.pack_start(text_label, expand=False)
        image_label = icon.small_image(self, extent)
        text_label = gtk.Label(u'<b>%s</b>' % label(extent))
        text_label.props.use_markup = True
        expander_label.pack_start(image_label, expand=False, padding=6)
        expander_label.pack_start(text_label, expand=False)
        expander = gtk.Expander()
        expander.props.label_widget = expander_label
        self.pack_start(expander, expand=False)
        vbox = gtk.VBox()
        expander.add(vbox)
        criteria = self._criteria = query_widget(db, query)
        vbox.pack_start(criteria, expand=False)
        # Update button.
        box = gtk.HBox()
        vbox.pack_start(box, expand=False)
        refresh = gtk.Button(stock=gtk.STOCK_REFRESH)
        refresh.connect('clicked', self.on_refresh_clicked)
        box.pack_end(refresh, expand=False)
        # Results table.
        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.pack_start(scroller, expand=True)
        results = self._results = Results(db, query)
        scroller.add_with_viewport(results)
        self.show_all()
        criteria.update_ui()
        results.rerun()

    def on_refresh_clicked(self, w):
        self._criteria.update_query()
        self._results.rerun()


class Results(gtk.VBox):

    def __init__(self, db, query):
        super(Results, self).__init__()
        self._db = db
        self._query = query
        self._class_expander = [
            # (Class, expander),
            ]

    def rerun(self):
        """Re-run the query and update results."""
        db = self._db
        # Destroy existing results.
        class_expander = self._class_expander
        while class_expander:
            class_, expander = class_expander.pop()
            expander.destroy()
        # Re-run query.
        results = self._query()
        class_results = {}
        for result in results:
            L = class_results.setdefault(result.__class__, [])
            L.append(result)
        # Create expanders and listviews.
        if not class_results:
            no_results = gtk.Label('No results found.')
            self.pack_start(no_results, expand=False)
            class_expander.append((None, no_results))
        for class_, results in class_results.iteritems():
            extent = class_._extent
            expander_label = gtk.HBox()
            # Label for extent.
            extent_image = icon.small_image(self, extent)
            count = len(results)
            if count != 1:
                extent_label = gtk.Label(
                    u'%i %s found:' % (count, plural(extent)))
            else:
                extent_label = gtk.Label(
                    u'%i %s found:' % (count, label(extent)))
            expander_label.pack_start(extent_image, expand=False, padding=6)
            expander_label.pack_start(extent_label, expand=False, padding=6)
            expander = gtk.Expander()
            expander.props.label_widget = expander_label
            expander.props.expanded = True
            self.pack_start(expander, expand=True)
            listview = ResultsListView(class_, results)
            expander.add(listview)
            class_expander.append((class_, expander))
        self.show_all()


class ResultsListView(ObjectList):

    def __init__(self, ResultClass, results):
        columns = []
        sorted = True
        for field_name, FieldClass in ResultClass._field_spec.iteritems():
            if not FieldClass.expensive:
                title = label(FieldClass)
                column = Column(field_name, title, data_type=str,
                                sorted=sorted)
                columns.append(column)
                sorted = False
        super(ResultsListView, self).__init__(columns, results)


## class ResultsTreeView(gtk.TreeView):

##     def __init__(self, ResultClass, results):
##         super(ResultsTreeView, self).__init__()
##         self._ResultClass = ResultClass
##         self._results = results
##         self._current_path = None
##         self._current_column = None
##         col_info = []
##         # Create model.
##         for field_name, FieldClass in ResultClass._field_spec.iteritems():
##             if not FieldClass.expensive:
##                 col_info.append((field_name, label(FieldClass)))
##         model = gtk.ListStore(object)
##         # Create columns.
##         for col_index, (field_name, field_label) in zip(
##             xrange(len(col_info)),
##             col_info,
##             ):
##             renderer = gtk.CellRendererText()
##             renderer.props.xalign = 0.0
##             column = gtk.TreeViewColumn(field_label, renderer)
##             column.set_cell_data_func(
##                 renderer, self._cell_data_func, (0, field_name))
##             self.append_column(column)
##         # Add data.
##         for result in results:
##             model.append([result])
##         self.set_model(model)
##         # Create popup window.
##         popup = self._popup = gtk.Window(gtk.WINDOW_POPUP)
##         # Respond to motion.
##         self.connect('leave-notify-event', self.on_leave_notify)
##         self.connect('motion-notify-event', self.on_motion_notify)
##         self.connect('path-cross-event', self._emit_cell_cross)
##         self.connect('column-cross-event', self._emit_cell_cross)
##         self.connect('cell-cross-event', self.on_cell_cross)

##     def on_cell_cross(self, treeview, event):
##         current_path, current_column, cell_x, cell_y, cell_x_, cell_y_ = (
##             self._current_cell_data(event))
##         popup = self._popup
##         if cell_x != None:
##             if popup.get_child():
##                 popup.get_child().destroy()
##             popup.add(self._tool_for(current_path))
##             popup_width, popup_height = popup.get_size()
##             pos_x, pos_y = self._tool_position(
##                 cell_x, cell_y, cell_x_, cell_y_, popup_width,
##                 popup_height, event)
##             popup.move(int(pos_x), int(pos_y))
##             popup.show_all()
##         else:
##             popup.hide()

##     def on_leave_notify(self, treeview, event):
##         self._current_column = None
##         self._current_path = None
##         self._popup.hide()

##     def on_motion_notify(self, treeview, event):
##         current_path, current_column = self._current_cell_data(event)[:2]
##         if self._current_path != current_path:
##             self._current_path = current_path
##             self.emit('path-cross-event', event)
##         if self._current_column != current_column:
##             self._current_column = current_column
##             self.emit('column-cross-event', event)

##     def _cell_data_func(self, column, cell, model, iter, col_key):
##         index, field_name = col_key
##         result = model.get_value(iter, index)
##         field = getattr(result.f, field_name)
##         cell.props.text = unicode(field)

##     def _current_cell_data(self, event):
##         try:
##             current_path, current_column = self.get_path_at_pos(
##                 int(event.x), int(event.y))[:2]
##         except:                         # XXX
##             return (None, None, None, None, None, None)
##         current_cell_area = self.get_cell_area(current_path, current_column)
##         treeview_root_coords = self.get_bin_window().get_origin()
##         cell_x = treeview_root_coords[0] + current_cell_area.x
##         cell_y = treeview_root_coords[1] + current_cell_area.y
##         cell_x_ = cell_x + current_cell_area.width
##         cell_y_ = cell_y + current_cell_area.height
##         return (current_path, current_column, cell_x, cell_y, cell_x_, cell_y_)

##     def _emit_cell_cross(self, treeview, event):
##         self.emit('cell-cross-event', event)

##     def _tool_for(self, path):
##         """Return a tool widget for ``result``."""
##         model = self.props.model
##         i = model.get_iter(path)
##         (result, ) = model.get(i, 0)
##         box = gtk.VBox()
##         box.pack_start(gtk.Label(unicode(result)))
##         box.show_all()
##         return box

##     def _tool_position(self, cell_x, cell_y, cell_x_, cell_y_, popup_width,
##                        popup_height, event):
##         screen_width = gtk.gdk.screen_width()
##         screen_height = gtk.gdk.screen_height()
##         pos_x = self.get_bin_window().get_origin()[0] + event.x + popup_width/2
##         if pos_x < 0:
##             pos_x = 0
##         elif pos_x + popup_width > screen_width:
##             pos_x = screen_width - popup_width
##         pos_y = cell_y_ + 3
##         if pos_y + popup_height > screen_height:
##             pos_y = cell_y - 3 - popup_height
##         return (pos_x, pos_y)


## for _name in ['path-cross-event', 'column-cross-event', 'cell-cross-event']:
##     gobject.signal_new(
##         _name, ResultsTreeView, gobject.SIGNAL_RUN_LAST,
##         gobject.TYPE_BOOLEAN, (gtk.gdk.Event, ))


# --------------------------------------------------------------------


@generic()
def query_widget(db, query):
    """Return the widget appropriate to ``query``."""


@query_widget.when("query in Q.Match")
def query_widget_match(db, query):
    return MatchForm(db=db, query=query)


@query_widget.when("query in Q.Intersection")
def query_widget_intersection(db, query):
    return IntersectionForm(db=db, query=query)


## @query_widget.when("query in Q.Union")
## def query_widget_union(db, query):
##     return UnionForm(db=db, query=query)


## @query_widget.when("query in Q.Group")
## def query_widget_group(db, query):
##     return GroupForm(db=db, query=query)


## @query_widget.when("query in Q.Min or query in Q.Max")
## def query_widget_minMax(db, query):
##     return MinMaxForm(db=db, query=query)


class IntersectionForm(gtk.Frame):

    def __init__(self, db, query):
        super(IntersectionForm, self).__init__(u'Intersection of')
        self._db = db
        self._query = query
        q_widget = self._query_widget = {}
        box = gtk.VBox()
        self.add(box)
        for subquery in query.queries:
            w = query_widget(db, subquery)
            q_widget[subquery] = w
            box.pack_start(w, expand=False)

    def update_query(self):
        for widget in self._query_widget.itervalues():
            widget.update_query()

    def update_ui(self):
        for widget in self._query_widget.itervalues():
            widget.update_ui()


FIELDLESS_OPERATORS = frozenset(
    (Q.o_any, Q.o_assigned, Q.o_in, Q.o_unassigned))


class MatchForm(gtk.HBox):

    def __init__(self, db, query):
        super(MatchForm, self).__init__()
        self._db = db
        self._query = query
        FieldClass = query.FieldClass
        # Field for value-based operators.
        field = self._field = FieldClass(query, query.field_name, query.value)
        # Label for the query's field.
        field_label = widget.FieldLabel(label(field))
        self.pack_start(field_label, expand=False)
        # Menu list for operator selection.
        opcombo = OperatorComboBox(query)
        self.pack_start(opcombo, expand=False)
        opcombo.connect('changed', self.on_opcombo_changed)
        # Field widget.
        controller = self._controller = gtk_field.Controller(db, field)
        field_widget = self._field_widget = controller.widget
        self.pack_start(field_widget, expand=True)
        field_widget.props.visible = query.operator not in FIELDLESS_OPERATORS

    def update_query(self):
        query = self._query
        self._controller.sync_field()
        if query.operator not in (Q.o_any, Q.o_unassigned, Q.o_in):
            query.value = self._field.get()

    def update_ui(self):
        operator = self._query.operator
        self._field_widget.props.visible = operator not in FIELDLESS_OPERATORS

    def on_opcombo_changed(self, w):
        operator = self._query.operator = w.current_operator
        self._field_widget.props.visible = operator not in FIELDLESS_OPERATORS


class OperatorComboBox(gtk.ComboBox):

    def __init__(self, query):
        model = gtk.ListStore(gobject.TYPE_STRING)
        super(OperatorComboBox, self).__init__(model)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        # Add operators.
        operators = self._operators = query.valid_operators
        current_operator = query.operator
        index = -1
        for operator in operators:
            index += 1
            self.append_text(label(operator))
            if operator is current_operator:
                self.set_active(index)

    @property
    def current_operator(self):
        active = self.get_active()
        return self._operators[active]


# Copyright (C) 2001-2005 Orbtech, L.L.C.
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
