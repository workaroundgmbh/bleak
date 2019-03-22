from typing import Union, List

from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.descriptor import BleakGATTDescriptor


class BleakGATTCharacteristicBlueZDBus(BleakGATTCharacteristic):
    """Interface for the Bleak representation of a GATT Characteristic"""

    def __init__(self, obj, object_path):
        super(BleakGATTCharacteristicBlueZDBus, self).__init__(obj)
        self.__descs = []
        self.__path = object_path


    @property
    def service_uuid(self) -> str:
        pass

    @property
    def uuid(self) -> str:
        return self.obj.get('UUID')

    @property
    def description(self) -> str:
        pass

    @property
    def properties(self) -> List:
        pass

    @property
    def descriptors(self) -> List:
        return self.__descs

    def get_descriptor(self, _uuid: str) -> Union[BleakGATTDescriptor, None]:
        pass

    @property
    def path(self):
        return self.__path

