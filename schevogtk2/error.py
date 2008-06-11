"""Error-message handling.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import gtk

import schevo.error


BULLET = u'\u2022 '


class FriendlyErrorDialog(object):

    def __init__(self, parent):
        self.parent = parent

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            show_error(self.parent, exc_val)
        if hasattr(sys, 'frozen'):
            # Ignore exception if running in py2exe environment.
            return True
        else:
            return False


def escape(s):
    s = (unicode(s)
         .replace('&', '&amp;')
         .replace('<', '&lt;')
         .replace('>', '&gt;')
         )
    return s


def show_error(parent, e):
    # Override for specific error types.
    if isinstance(e, schevo.error.DeleteRestricted):
        markup = [
            u'The object was not deleted from the database.\n'
            u'\n'
            u'It is referred to by the following objects,\n'
            u'which require you to delete them first before\n'
            u'deleting this object.\n'
            u'\n'
            ]
        for entity, referring_entity, referring_field_name in e.restrictions:
            markup.append(BULLET + '<b>%s</b>\n' % escape(entity))
    elif isinstance(e, schevo.error.KeyCollision):
        markup = [
            u'Your changes were not saved.\n'
            u'\n'
            u'There is already an object of this type that has\n'
            u'the following values, which must be unique:\n'
            u'\n'
            ]
        for field_name, field_value in zip(e.key_spec, e.field_values):
            markup.append(BULLET + '<b>%s</b>: %s'
                          % (escape(field_name), escape(field_value)))
    elif isinstance(e, schevo.error.TransactionRuleViolation):
        markup = [
            u'Your changes were not saved.\n'
            u'\n'
            u'The following transaction rule was violated when\n'
            u'attempting to save:\n'
            u'\n'
            ]
        markup.append(BULLET + u'<b>%s</b>\n' % escape(e.message))
    elif isinstance(e, schevo.error.TransactionFieldsNotChanged):
        markup = [
            u'No fields changed.\n'
            u'\n'
            u'Change at least one field to update this object,\n'
            u'or click <b>Cancel</b> to leave it unchanged.\n'
            ]
    else:
        # By default, just show the error message verbatim.
        markup = [escape(str(e))]
    markup = u''.join(markup)
    # Show the dialog.
    flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
    win = gtk.MessageDialog(parent=parent, flags=flags,
                            type=gtk.MESSAGE_ERROR,
                            buttons=gtk.BUTTONS_CLOSE)
    win.set_markup(markup)
    win.run()
    win.destroy()


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
