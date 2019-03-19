# -*- coding: utf-8 -*-
"""
Interface class for the Bleak representation of a GATT Service

Created on 2019-03-19 by hbldh <henrik.blidh@nedomkull.com>

"""
import abc
from typing import List, Union

from bleak.uuids import uuidstr_to_str
from bleak.backends.characteristic import BleakGATTCharacteristic


class BleakGATTService(abc.ABC):
    """Interface for the Bleak representation of a GATT Service

    - When using Windows backend, `details` attribute is a
      `Windows.Devices.Enumeration.DeviceInformation` object.
    - When using Linux backend, `details` attribute is a
      string path to the DBus device object.
    - When using macOS backend, `details` attribute will be
      something else.

    """

    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return "{0}: {1}".format(self.uuid, self.description)

    @property
    @abc.abstractmethod
    def uuid(self) -> str:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def description(self) -> str:
        return uuidstr_to_str(self.uuid)

    @property
    @abc.abstractmethod
    def characteristics(self) -> List:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_characteristic(self, _uuid) -> Union[BleakGATTCharacteristic, None]:
        raise NotImplementedError()
