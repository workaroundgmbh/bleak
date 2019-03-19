from typing import List

from bleak.uuids import uuidstr_to_str
from bleak.backends.service import BleakGATTService
from bleak.backends.dotnet.characteristic import BleakGATTCharacteristicDotNet

from Windows.Devices.Bluetooth.GenericAttributeProfile import GattDeviceService


class BleakGATTServiceDotNet(BleakGATTService):

    def __init__(self, obj: GattDeviceService):
        super().__init__(obj)
        self.__chars = [BleakGATTCharacteristicDotNet(c) for c in obj.GetAllCharacteristics()]

    @property
    def uuid(self):
        return self.obj.Uuid.ToString()

    @property
    def description(self):
        return super(BleakGATTServiceDotNet, self).description

    @property
    def characteristics(self) -> List:
        return self.__chars

    def get_characteristic(self, _uuid):
        pass
