"""SchevoGtk constants."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

import pango


MONO_FONT = pango.FontDescription('monospace normal')


optimize.bind_all(sys.modules[__name__])  # Last line of module.
