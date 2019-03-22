from typing import Union, List

from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.descriptor import BleakGATTDescriptor


class BleakGATTCharacteristicBlueZDBus(BleakGATTCharacteristic):
    """Interface for the Bleak representation of a GATT Characteristic"""

    def __init__(self, obj, object_path, service_uuid):
        super(BleakGATTCharacteristicBlueZDBus, self).__init__(obj)
        self.__descs = []
        self.__path = object_path
        self.__service_uuid = service_uuid

    @property
    def service_uuid(self) -> str:
        return self.__service_uuid

    @property
    def uuid(self) -> str:
        return self.obj.get('UUID')

    @property
    def description(self) -> str:
        # No description available in DBus backend.
        return ""

    @property
    def properties(self) -> List:
        return self.obj['Flags']

    @property
    def descriptors(self) -> List:
        return self.__descs

    def get_descriptor(self, _uuid: str) -> Union[BleakGATTDescriptor, None]:
        try:
            return next(filter(lambda x: x.uuid == _uuid, self.descriptors))
        except StopIteration:
            return None

    def add_descriptor(self, descriptor: BleakGATTDescriptor):
        self.__descs.append(descriptor)

    @property
    def path(self):
        return self.__path

