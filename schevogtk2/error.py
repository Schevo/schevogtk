"""Error-message handling."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from StringIO import StringIO
from traceback import print_exception

import gtk

from schevo.placeholder import Placeholder
import schevo.error
from schevo.label import label, plural

from schevogtk2.constants import MONO_FONT


BULLET = u'\u2022 '


# List of functions of signature fn(exc_type, exc_val, exc_tb) that
# handle an error and return a list of string in marked-up form to
# join together in the dialog, or skip handling of an error and return
# None.
ERROR_HANDLERS = [
    ]


class FriendlyErrorDialog(object):

    def __init__(self, parent, always_ignore=True):
        self.parent = parent
        self.always_ignore = always_ignore

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            show_error(self.parent, exc_type, exc_val, exc_tb)
        if hasattr(sys, 'frozen'):
            # Ignore exception if running in py2exe environment.
            return self.always_ignore
        else:
            return False


def dereference(obj):
    if isinstance(obj, Placeholder) and obj.entity is not None:
        return obj.entity
    else:
        return obj


def escape(s):
    s = (unicode(s)
         .replace('&', '&amp;')
         .replace('<', '&lt;')
         .replace('>', '&gt;')
         )
    return s


def show_error(parent, exc_type, exc_val, exc_tb):
    try:
        markup = None
        for handler in ERROR_HANDLERS:
            markup = handler(exc_type, exc_val, exc_tb)
            if markup is not None:
                break
        if markup is None:
            if issubclass(exc_type, schevo.error.DatabaseFileLocked):
                markup = [
                    u'The file or library you are trying to open is already\n'
                    u'in use by another application.  Please close the file\n'
                    u'in the other application to open it here.\n'
                    ]
            elif issubclass(exc_type, schevo.error.DeleteRestricted):
                markup = [
                    u'The object was not deleted from the database.\n'
                    u'\n'
                    u'It is referred to by the following types of objects.\n'
                    u'Delete them first before deleting this object.\n'
                    u'\n'
                    ]
                restrictions = sorted(exc_val.restrictions)
                ref_extents = set()
                for entity, ref_entity, ref_field_name in restrictions:
                    ref_extents.add(ref_entity.s.extent)
                for extent in sorted(ref_extents):
                    markup.append(BULLET + '<b>%s</b>\n' % plural(extent))
            elif issubclass(exc_type, schevo.error.FieldReadonly):
                markup = [
                    u'The <b>%s</b> field is readonly and cannot be changed.'
                    % escape(label(exc_val.field))
                    ]
            elif issubclass(exc_type, schevo.error.FieldRequired):
                markup = [
                    u'The <b>%s</b> field is required. Please provide a value.'
                    % escape(label(exc_val.field))
                    ]
            elif issubclass(exc_type, schevo.error.KeyCollision):
                markup = [
                    u'Your changes were not saved.\n'
                    u'\n'
                    u'There is already an object of this type that has\n'
                    u'the following values, which must be unique:\n'
                    u'\n'
                    ]
                for field_name, field_value in zip(exc_val.key_spec,
                                                   exc_val.field_values):
                    markup.append(BULLET + '<b>%s</b>: %s\n'
                                  % (escape(field_name),
                                     escape(dereference(field_value))))
            elif issubclass(exc_type, schevo.error.TransactionExpired):
                markup = [
                    u'The transaction has expired.\n'
                    u'\n'
                    u'The most common reason for this is performing\n'
                    u'another transaction that results in this object\n'
                    u'being updated.\n'
                    u'\n'
                    u'Cancel this transaction, then re-open it, to\n'
                    u'complete the desired operation.'
                    ]
            elif issubclass(exc_type, schevo.error.TransactionRuleViolation):
                markup = [
                    u'Your changes were not saved.\n'
                    u'\n'
                    u'The following transaction rule was violated when\n'
                    u'attempting to save:\n'
                    u'\n'
                    ]
                markup.append(BULLET + u'<b>%s</b>\n' % escape(exc_val.message))
            elif issubclass(exc_type, schevo.error.TransactionFieldsNotChanged):
                markup = [
                    u'No fields changed.\n'
                    u'\n'
                    u'Change at least one field to update this object,\n'
                    u'or click <b>Cancel</b> to leave it unchanged.'
                    ]
            else:
                # By default, just show the error message verbatim.
                markup = [escape(str(exc_val))]
        markup = u''.join(markup)
    except:
        markup = 'See "Diagnostics" tab for information.'
    # Show the dialog.
    flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
    win = ErrorMessage(title='ATFG Error', parent=parent, flags=flags,
                       buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT),
                       markup=markup,
                       exc_type=exc_type, exc_val=exc_val, exc_tb=exc_tb)
    win.run()
    win.destroy()


class ErrorMessage(gtk.Dialog):

    def __init__(self, title=None, parent=None, flags=None, buttons=None,
                 markup=None, exc_type=None, exc_val=None, exc_tb=None):
        gtk.Dialog.__init__(self, title, parent, flags, buttons)
        self.props.width_request = 400
        self.props.height_request = 300
        # Notebook.
        notebook = gtk.Notebook()
        notebook.show()
        self.vbox.pack_start(notebook)
        # Message.
        message = gtk.Label()
        message.props.selectable = True
        message.set_markup(markup)
        message.show()
        notebook.append_page(message, gtk.Label('Message'))
        # Traceback.
        traceback_scrolled = gtk.ScrolledWindow()
        traceback_scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        traceback_scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        traceback_scrolled.show()
        traceback_textview = gtk.TextView()
        traceback_textview.props.editable = False
        traceback_textview.modify_font(MONO_FONT)
        traceback_file = StringIO()
        print_exception(exc_type, exc_val, exc_tb, None, traceback_file)
        traceback_text = traceback_file.getvalue()
        traceback_textview.get_buffer().insert_at_cursor(
            traceback_text, len(traceback_text))
        traceback_textview.show()
        traceback_scrolled.add(traceback_textview)
        notebook.append_page(traceback_scrolled, gtk.Label('Diagnostics'))


optimize.bind_all(sys.modules[__name__])  # Last line of module.
