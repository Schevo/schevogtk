"""schevogtk2 / schevo.icon integration.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import weakref

import gtk

from schevo.base import Database
from schevo.base import Extent


_db_map = weakref.WeakKeyDictionary()


_stock_map = {
    'db.execute': gtk.STOCK_EXECUTE,
    'q.default': gtk.STOCK_FIND,
    't.create': gtk.STOCK_ADD,
    't.delete': gtk.STOCK_DELETE,
    't.update': gtk.STOCK_EDIT,
    'v.default': gtk.STOCK_ZOOM_IN,
    }


def iconset(widget, *args):
    """Return a gtk.IconSet for the database object `obj`."""
    # Find database from obj.
    if isinstance(args[0], Database):
        db, name = args
    elif isinstance(args[0], Extent):
        extent = args[0]
        db = extent.db
        name = u'db.%s' % extent.name
    else:
        # Could not find object.
        return gtk.IconSet()
    # Make sure database supports icons.
    if not hasattr(db, '_icon'):
        return gtk.IconSet()
    return _iconset(widget, db, name)


def large_image(widget, *args):
    """Return a large-size gtk.Image for the object."""
    iset = iconset(widget, *args)
    return gtk.image_new_from_icon_set(iset, gtk.ICON_SIZE_LARGE_TOOLBAR)


def small_image(widget, *args):
    """Return a large-size gtk.Image for the object."""
    iset = iconset(widget, *args)
    return gtk.image_new_from_icon_set(iset, gtk.ICON_SIZE_SMALL_TOOLBAR)


def large_pixbuf(widget, *args):
    """Return a large-size Pixbuf for the object."""
    iset = iconset(widget, *args)
    return iset.render_icon(
        style=widget.get_style(),
        direction=gtk.TEXT_DIR_NONE,
        state=gtk.STATE_NORMAL,
        size=gtk.ICON_SIZE_LARGE_TOOLBAR,
        widget=None,
        detail=None,
        )


def small_pixbuf(widget, *args):
    """Return a small-size Pixbuf for the object."""
    iset = iconset(widget, *args)
    return iset.render_icon(
        style=widget.get_style(),
        direction=gtk.TEXT_DIR_NONE,
        state=gtk.STATE_NORMAL,
        size=gtk.ICON_SIZE_SMALL_TOOLBAR,
        widget=None,
        detail=None,
        )


def _iconset(widget, db, name):
    """Return an IconSet for an extent."""
    name_iconset = _db_map.setdefault(db, {})
    style = None
    if hasattr(widget, 'get_style'):
        style = widget.get_style()
    if (style, name) in name_iconset:
        return name_iconset[(style, name)]
    else:
        data = db._icon(name, use_default=False)
        if data is None:
            if name in _stock_map:
                stock_id = _stock_map[name]
            else:
                stock_id = gtk.STOCK_FILE
            iset = style.lookup_icon_set(stock_id)
        else:
            loader = gtk.gdk.PixbufLoader()
            loader.write(data)
            loader.close()
            pixbuf = loader.get_pixbuf()
            iset = gtk.IconSet(pixbuf)
        name_iconset[(style, name)] = iset
        return iset


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2005 Orbtech, L.L.C.
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
