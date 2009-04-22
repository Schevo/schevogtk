"""Dialog helpers."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

import gtk

if sys.platform == 'win32':
    import pywintypes
    import win32con
    import win32gui


def _patterns_to_win32_filter(description, patterns):
    return '%s\0%s\0' % (description, ';'.join(patterns))


WIN32_CUSTOM_FILTER = 'All Files\0*.*\0'


def open(title, parent=None, patterns=[], description='',
         filter=None, folder='.', default_extension=''):
    """Display an open dialog and return a filename."""
    if sys.platform == 'win32':
        path = None
        win32filter = _patterns_to_win32_filter(description, patterns)
        try:
            path, custom_filter, flags = win32gui.GetOpenFileNameW(
                InitialDir=folder,
                Flags=win32con.OFN_EXPLORER|win32con.OFN_FILEMUSTEXIST,
                File='',
                DefExt=default_extension,
                Title=title,
                Filter=win32filter,
                CustomFilter=WIN32_CUSTOM_FILTER,
                FilterIndex=1,
                )
        except pywintypes.error:
            # Cancel button raises an exception.
            pass
        return path
    else:
        filechooser = gtk.FileChooserDialog(
            title, parent,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
             gtk.STOCK_OPEN, gtk.RESPONSE_OK),
            )
        if patterns or filter:
            if not filter:
                filter = gtk.FileFilter()
                for pattern in patterns:
                    filter.add_pattern(pattern)
            filechooser.set_filter(filter)
        filechooser.set_default_response(gtk.RESPONSE_OK)
        if folder:
            filechooser.set_current_folder(folder)
        response = filechooser.run()
        if response != gtk.RESPONSE_OK:
            filechooser.destroy()
            return
        path = filechooser.get_filename()
        filechooser.destroy()
        return path


def save(title, parent=None, patterns=[], description='',
         filter=None, folder='.', default_extension=''):
    """Display an open dialog and return a filename."""
    if sys.platform == 'win32':
        path = None
        win32filter = _patterns_to_win32_filter(description, patterns)
        try:
            path, custom_filter, flags = win32gui.GetSaveFileNameW(
                InitialDir=folder,
                Flags=win32con.OFN_EXPLORER|win32con.OFN_OVERWRITEPROMPT,
                File='',
                DefExt=default_extension,
                Title=title,
                Filter=win32filter,
                CustomFilter=WIN32_CUSTOM_FILTER,
                FilterIndex=1,
                )
        except pywintypes.error:
            # Cancel button raises an exception.
            pass
        return path
    else:
        filechooser = gtk.FileChooserDialog(
            title, parent,
            gtk.FILE_CHOOSER_ACTION_SAVE,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
             gtk.STOCK_SAVE, gtk.RESPONSE_OK),
            )
        if patterns or filter:
            if not filter:
                filter = gtk.FileFilter()
                for pattern in patterns:
                    filter.add_pattern(pattern)
            filechooser.set_filter(filter)
        filechooser.set_default_response(gtk.RESPONSE_OK)
        if folder:
            filechooser.set_current_folder(folder)
        response = filechooser.run()
        if response != gtk.RESPONSE_OK:
            filechooser.destroy()
            return
        path = filechooser.get_filename()
        filechooser.destroy()
        return path


optimize.bind_all(sys.modules[__name__])  # Last line of module.
