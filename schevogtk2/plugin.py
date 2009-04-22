"""Plugin support for customizing the default behavior."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

custom_tx_dialog_handlers = []
custom_view_dialog_handlers = []

def add_custom_tx_dialog_handler(handler):
    custom_tx_dialog_handlers.append(handler)

def get_custom_tx_dialog_class(db, action):
    for handler in custom_tx_dialog_handlers:
        customClass = handler(db, action)
        if customClass is not None:
            return customClass


def add_custom_view_dialog_handler(handler):
    custom_view_dialog_handlers.append(handler)

def get_custom_view_dialog_class(db, action):
    for handler in custom_view_dialog_handlers:
        customClass = handler(db, action)
        if customClass is not None:
            return customClass


optimize.bind_all(sys.modules[__name__])  # Last line of module.
