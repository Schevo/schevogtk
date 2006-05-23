"""Gazpacho integration: loader and extensions"""

# Set up the kiwi environment, using brute force evilness.
from kiwi.environ import environ
import os
import sys
if hasattr(sys, 'frozen'):
    root = os.path.dirname(sys.executable)
else:
    import schevo.gtk
    root = schevo.gtk.__path__[0]
environ._root = root  # XXX Evil hackery.
environ.add_resource(resource='glade', path='glade')


import gettext

## import gobject
## import gtk

from gazpacho.loader.custom import (
    Adapter, PythonWidgetAdapter, adapter_registry)

from kiwi.log import Logger

# Schevo widgets.
from schevo.gtk.entitygrid import EntityGrid
from schevo.gtk.extentgrid import ExtentGrid
from schevo.gtk.field import FieldLabel
from schevo.gtk.field import DynamicField
from schevo.gtk.relatedgrid import RelatedGrid


_ = gettext.gettext

log = Logger('gazpacholoader')


class EntityGridAdapter(PythonWidgetAdapter):
    object_type = EntityGrid
    def construct(self, name, gtype, properties):
        return super(EntityGridAdapter, self).construct(name, gtype,
                                                        properties)
adapter_registry.register_adapter(EntityGridAdapter)


class ExtentGridAdapter(PythonWidgetAdapter):
    object_type = ExtentGrid
    def construct(self, name, gtype, properties):
        return super(ExtentGridAdapter, self).construct(name, gtype,
                                                        properties)
adapter_registry.register_adapter(ExtentGridAdapter)


class FieldLabelAdapter(PythonWidgetAdapter):
    object_type = FieldLabel
    def construct(self, name, gtype, properties):
        return super(FieldLabelAdapter, self).construct(name, gtype,
                                                        properties)
adapter_registry.register_adapter(FieldLabelAdapter)


class DynamicFieldAdapter(PythonWidgetAdapter):
    object_type = DynamicField
    def construct(self, name, gtype, properties):
        return super(DynamicFieldAdapter, self).construct(name, gtype,
                                                          properties)
adapter_registry.register_adapter(DynamicFieldAdapter)


class RelatedGridAdapter(PythonWidgetAdapter):
    object_type = RelatedGrid
    def construct(self, name, gtype, properties):
        return super(RelatedGridAdapter, self).construct(name, gtype,
                                                        properties)
adapter_registry.register_adapter(RelatedGridAdapter)


