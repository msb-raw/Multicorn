# -*- coding: utf-8 -*-
# This file is part of Dyko
# Copyright © 2008-2009 Kozea
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kalamar.  If not, see <http://www.gnu.org/licenses/>.

"""
Parsers for databases.

"""

from kalamar.storage import base
from kalamar.item import CapsuleItem

class DBCapsule(CapsuleItem):
    """A capsule format for items stored in databases.
    
    This parser can store capsules in databases without additional public
    access points.
    
    A table is needed in the same database as the capsule (but not necessarily
    in the same database as the subitems). This table is called the linking
    table, as it links the capsule access point and the item access point.
    
    """
    # TODO: make this capsule ordered
    format = 'db_capsule'

    def __init__(self, access_point, opener=None, storage_properties={}):
        """DBCapsule instance initialisation."""
        super(DBCapsule, self).__init__(
            access_point, opener, storage_properties)
        self._link_ap = None
    
    def _load_subitems(self):
        """Load and return capsule subitems.
        
        This function also creates a private access point for the linking
        table.

        """
        # TODO: capsule table name and capsule ap name should be different
        # TODO: linking table name/url should be configurable
        # TODO: keys in linking table should be configurable
        capsule_url = self._access_point.config['url']
        capsule_table_name = capsule_url.split('?')[-1]
        foreign_access_point_name =
            self._access_point.config['foreign_access_point']
        link_access_point_name = self._access_point.config['link_access_point']

        # Create an access point if not already done
        if not self._link_ap:
            self._link_ap = 
                self._access_point.site.access_points[link_access_point_name]
            keys = self._link_ap.get_storage_properties()
            self.capsule_keys = [
                key for key in keys if key.startswith(capsule_table_name)
            ]
            self.foreign_keys = [
                key for key in keys if key.startswith(foreign_access_point_name)
            ]

        # Search items in link table matching self keys
        request = '/'.join([
                '%s=%s' % (key, self[key.split('_', 1)[1]])
                for key in self.capsule_keys])
        items = self._access_point.site.search(link_access_point_name, request)

        # Return items in foreign table matching link item keys
        for item in items:
            request = '/'.join([
                    '%s=%s' % (key.split('_', 1)[1], item[key])
                    for key in self.foreign_keys])
            yield self._access_point.site.open(
                foreign_access_point_name,
                request
            )

    def serialize(self):
        """Save all subitems in the linking table."""
        for subitem in self.subitems:
            properties = {}

            for key in self.capsule_keys:
                properties[key] = self[key.split('_', 1)[1]]
            
            for key in self.foreign_keys:
                properties[key] = subitem[key.split('_', 1)[1]]

            item = self._access_point.site.create_item(
                self._link_ap.config['name'], properties)
            self._access_point.site.save(item)
