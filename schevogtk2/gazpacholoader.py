"""Gazpacho integration: loader and extensions"""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

# Set up the kiwi environment, using brute force evilness.
from kiwi.environ import environ
import os
import sys
if hasattr(sys, 'frozen'):
    root = os.path.dirname(sys.executable)
else:
    import schevogtk2
    root = schevogtk2.__path__[0]
environ._root = root  # XXX Evil hackery.
environ.add_resource(resource='glade', path='glade')


from gazpacho.loader.custom import (
    Adapter, PythonWidgetAdapter, adapter_registry)


# Schevo widgets.
from schevogtk2.entitygrid import EntityGrid
from schevogtk2.extentgrid import ExtentGrid
from schevogtk2.field import FieldLabel
from schevogtk2.field import DynamicField
from schevogtk2.relatedgrid import RelatedGrid


class EntityGridAdapter(PythonWidgetAdapter):
    object_type = EntityGrid
    def construct(self, name, gtype, properties):
        return PythonWidgetAdapter.construct(self, name, gtype, properties)
adapter_registry.register_adapter(EntityGridAdapter)


class ExtentGridAdapter(PythonWidgetAdapter):
    object_type = ExtentGrid
    def construct(self, name, gtype, properties):
        return PythonWidgetAdapter.construct(self, name, gtype, properties)
adapter_registry.register_adapter(ExtentGridAdapter)


class FieldLabelAdapter(PythonWidgetAdapter):
    object_type = FieldLabel
    def construct(self, name, gtype, properties):
        return PythonWidgetAdapter.construct(self, name, gtype, properties)
adapter_registry.register_adapter(FieldLabelAdapter)


class DynamicFieldAdapter(PythonWidgetAdapter):
    object_type = DynamicField
    def construct(self, name, gtype, properties):
        return PythonWidgetAdapter.construct(self, name, gtype, properties)
adapter_registry.register_adapter(DynamicFieldAdapter)


class RelatedGridAdapter(PythonWidgetAdapter):
    object_type = RelatedGrid
    def construct(self, name, gtype, properties):
        return PythonWidgetAdapter.construct(self, name, gtype, properties)
adapter_registry.register_adapter(RelatedGridAdapter)


