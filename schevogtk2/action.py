"""Action class and helper functions.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo.base import Entity, Extent, View
from schevo.label import label


DEFAULT_T_METHODS = ['clone', 'create', 'delete', 'update']


class Action(object):

    instance = None
    label = ''
    method = None
    name = ''
    related = None
    type = ''

    def __cmp__(self, other):
        try:
            return cmp(self.label, other.label)
        except AttributeError:
            return cmp(hash(self), hash(other))

def get_method_action(instance, namespace_id, method_name, related=None):
    """Return action for method name."""
    namespace = getattr(instance, namespace_id)
    method = namespace[method_name]
    method_label = label(method)
    action = Action()
    action.instance = instance
    # Default label.
    action.label = u'%s...' % method_label
    if namespace_id == 't' and method_name in DEFAULT_T_METHODS:
        # Determine if there are any custom methods whose labels start
        # with the same string.
        t = action.instance.t
        other_found = False
        for other_name in t:
            if other_name not in DEFAULT_T_METHODS:
                other_label = label(t[other_name])
                if other_label.startswith(method_label):
                    other_found = True
        if other_found:
            # Custom labels, since there are custom methods that share
            # prefixes.
            if isinstance(instance, Entity):
                action.label = u'%s %s...' % (
                    method_label, label(instance.sys.extent))
            elif isinstance(instance, Extent):
                action.label = u'%s %s...' % (method_label, label(instance))
            elif isinstance(instance, View):
                action.label = u'%s %s...' % (
                    method_label, label(instance.sys.entity.sys.extent))
    action.method = method
    action.name = method_name
    action.related = related
    if namespace_id == 'q':
        action.type = 'query'
    elif namespace_id == 't':
        action.type = 'transaction'
    return action

def get_relationship_actions(entity):
    """Return list of relationship actions for an entity instance."""
    actions = []
    if entity is not None:
        items = []
        if entity.sys.extent.relationships:
            items = [
                'Relationships...',
                ]
        for text in items:
            action = Action()
            action.instance = entity
            action.label = text
            action.name = 'relationship'
            action.type = 'relationship'
            actions.append(action)
    return sorted(actions)

def get_tx_actions(instance, related=None):
    """Return list of actions for an extent or entity instance."""
    actions = []
    if instance is not None:
        t_methods = set(instance.t)
        for method_name in sorted(t_methods):
            action = get_method_action(instance, 't', method_name, related)
            actions.append(action)
    return sorted(actions)

def get_view_actions(entity):
    """Return list of view actions for an entity instance."""
    actions = []
    if 'default' in entity._hidden_views:
        return actions
    if entity is not None:
        options = [False]
        for name, FieldClass in entity._field_spec.iteritems():
            if FieldClass.expensive:
                # XXX: Remove this and add support for View objects.
##                 options.append(True)
                break
        for include_expensive in options:
            action = get_view_action(entity, include_expensive)
            actions.append(action)
    return sorted(actions)

def get_view_action(entity, include_expensive):
    if include_expensive:
        text = u'View (including expensive fields)...'
    else:
        text = u'View...'
    action = Action()
    action.include_expensive = include_expensive
    action.instance = entity
    action.label = text
    action.name = 'view'
    action.type = 'view'
    return action


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
