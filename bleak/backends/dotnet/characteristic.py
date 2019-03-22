# -*- coding: utf-8 -*-
"""
Interface class for the Bleak representation of a GATT Characteristic

Created on 2019-03-19 by hbldh <henrik.blidh@nedomkull.com>

"""
from typing import List, Union

from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.dotnet.descriptor import BleakGATTDescriptorDotNet

from Windows.Devices.Bluetooth.GenericAttributeProfile import GattCharacteristic

# Python representation of <class 'Windows.Devices.Bluetooth.GenericAttributeProfile.GattCharacteristicProperties'>
# TODO: Formalize this to Enum for all backends.
_GattCharacteristicsPropertiesEnum = {
    None: ("None", "The characteristic doesn’t have any properties that apply"),
    1: ("Broadcast", "The characteristic supports broadcasting"),
    2: ("Read", "The characteristic is readable"),
    4: ("WriteWithoutResponse", "The characteristic supports Write Without Response"),
    8: ("Write", "The characteristic is writable"),
    16: ("Notify", "The characteristic is notifiable"),
    32: ("Indicate", "The characteristic is indicatable"),
    64: ("AuthenticatedSignedWrites", "The characteristic supports signed writes"),
    128: ("ExtendedProperties", "The ExtendedProperties Descriptor is present"),
    256: ("ReliableWrites", "The characteristic supports reliable writes"),
    512: ("WritableAuxiliaries", "The characteristic has writable auxiliaries"),
}


class BleakGATTCharacteristicDotNet(BleakGATTCharacteristic):
    """Interface for the Bleak representation of a GATT Characteristic"""


    def __init__(self, obj: GattCharacteristic):
        super().__init__(obj)
        self.__desc = [
            BleakGATTDescriptorDotNet(d, self.uuid) for d in obj.GetAllDescriptors()
        ]
        self.__props = [
            _GattCharacteristicsPropertiesEnum[v][0]
            for v in [2 ** n for n in range(10)]
            if (self.obj.CharacteristicProperties & v)
        ]

    def __str__(self):
        return "{0}: {1}".format(self.uuid, self.description)

    @property
    def service_uuid(self) -> str:
        return self.obj.Service.Uuid.ToString()

    @property
    def uuid(self) -> str:
        return self.obj.Uuid.ToString()

    @property
    def description(self) -> str:
        return self.obj.UserDescription

    @property
    def properties(self) -> List:
        return self.__props

    @property
    def descriptors(self) -> List:
        return self.__desc

    def get_descriptor(self, _uuid) -> Union[BleakGATTDescriptorDotNet, None]:
        try:
            return next(filter(lambda x: x.uuid == _uuid, self.descriptors))
        except StopIteration:
            return None

    def add_descriptor(self, _uuid: str):
        pass

