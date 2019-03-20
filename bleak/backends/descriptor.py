# -*- coding: utf-8 -*-
"""
Interface class for the Bleak representation of a GATT Descriptor

Created on 2019-03-19 by hbldh <henrik.blidh@nedomkull.com>

"""
import abc
from typing import Any


class BleakGATTDescriptor(abc.ABC):
    """Interface for the Bleak representation of a GATT Descriptor"""

    def __init__(self, obj: Any):
        self.obj = obj

    def __str__(self):
        return "{0}: {1}".format(self.uuid, self.description)

    @property
    @abc.abstractmethod
    def characteristic_uuid(self) -> str:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def uuid(self) -> str:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def handle(self) -> int:
        raise NotImplementedError()
