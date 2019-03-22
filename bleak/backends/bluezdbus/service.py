from typing import Union, List

from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.service import BleakGATTService


class BleakGATTServiceBlueZDBus(BleakGATTService):

    def __init__(self, obj):
        super().__init__(obj)
        self.__chars = []

    @property
    def uuid(self) -> str:
        return self.obj['UUID']

    @property
    def description(self) -> str:
        return super(BleakGATTServiceBlueZDBus, self).description

    @property
    def characteristics(self) -> List:
        return self.__chars

    def get_characteristic(self, _uuid) -> Union[BleakGATTCharacteristic, None]:
        raise NotImplementedError()
