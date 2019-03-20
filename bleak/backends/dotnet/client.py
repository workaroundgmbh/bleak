# -*- coding: utf-8 -*-
"""
BLE Client for Windows 10 systems.

Created on 2017-12-05 by hbldh <henrik.blidh@nedomkull.com>
"""

import logging
import asyncio
from asyncio.events import AbstractEventLoop
from functools import wraps
from typing import Callable, Any

from bleak.backends.dotnet.service import BleakGATTServiceDotNet
from bleak.exc import BleakError, BleakDotNetTaskError
from bleak.backends.client import BaseBleakClient
from bleak.backends.dotnet.discovery import discover
from bleak.backends.dotnet.utils import wrap_Task, wrap_IAsyncOperation

# CLR imports
# Import of Bleak CLR->UWP Bridge.
from BleakBridge import Bridge

# Import of other CLR components needed.
from System import Array, Byte
from Windows.Foundation import IAsyncOperation, TypedEventHandler
from Windows.Storage.Streams import DataReader, DataWriter, IBuffer
from Windows.Devices.Bluetooth import BluetoothLEDevice, BluetoothConnectionStatus, BluetoothCacheMode
from Windows.Devices.Bluetooth.GenericAttributeProfile import (
    GattDeviceService,
    GattDeviceServicesResult,
    GattCharacteristic,
    GattCharacteristicsResult,
    GattDescriptor,
    GattDescriptorsResult,
    GattCommunicationStatus,
    GattReadResult,
    GattWriteResult,
    GattValueChangedEventArgs,
    GattCharacteristicProperties,
    GattClientCharacteristicConfigurationDescriptorValue
)

logger = logging.getLogger(__name__)


class BleakClientDotNet(BaseBleakClient):
    """The .NET Bleak Client."""

    def __init__(self, address: str, loop: AbstractEventLoop = None, **kwargs):
        super(BleakClientDotNet, self).__init__(address, loop, **kwargs)

        # Backend specific. Python.NET objects.
        self._device_info = None
        self._requester = None
        self._bridge = Bridge()
        self._callbacks = {}

        self.service_objects = []

    def __str__(self):
        return "BleakClientDotNet ({0})".format(self.address)

    # Connectivity methods

    async def connect(self) -> bool:
        """Connect the BleakClient to the BLE device.

        Returns:
            Boolean from :meth:`~is_connected`.

        """
        # Try to find the desired device.
        devices = await discover(2.0, loop=self.loop)
        sought_device = list(
            filter(lambda x: x.address.upper() == self.address.upper(), devices)
        )

        if len(sought_device):
            self._device_info = sought_device[0].details
        else:
            raise BleakError(
                "Device with address {0} was " "not found.".format(self.address)
            )

        logger.debug("Connecting to BLE device @ {0}".format(self.address))
        self._requester = await wrap_IAsyncOperation(
            IAsyncOperation[BluetoothLEDevice](
                BluetoothLEDevice.FromIdAsync(self._device_info.Id)
            ),
            return_type=BluetoothLEDevice,
            loop=self.loop,
        )

        def _ConnectionStatusChanged_Handler(sender, args):
            logger.debug("_ConnectionStatusChanged_Handler: " + args.ToString())

        self._requester.ConnectionStatusChanged += _ConnectionStatusChanged_Handler

        # Obtain services, which also leads to connection being established.
        await self.get_services()
        await asyncio.sleep(0.2, loop=self.loop)
        connected = await self.is_connected()
        if connected:
            logger.debug("Connection successful.")
        else:
            raise BleakError(
                "Connection to {0} was not successful!".format(self.address)
            )

        return connected

    async def disconnect(self) -> bool:
        logger.debug("Disconnecting from BLE device...")
        # Remove notifications
        # TODO: Make sure all notifications are removed prior to Dispose.
        # Dispose all components that we have requested and created.
        for service_uuid, service in self.services.items():
            service.Dispose()
        self.services = None
        self._requester.Dispose()
        self._requester = None

        return not await self.is_connected()

    async def is_connected(self) -> bool:
        if self._requester:
            return (
                self._requester.ConnectionStatus == BluetoothConnectionStatus.Connected
            )

        else:
            return False

    # GATT services methods

    async def get_services(self) -> dict:
        # Return a list of all services for the device.
        if self.services:
            return self.services
        else:
            logger.debug("Get Services...")
            services_result = await wrap_IAsyncOperation(
                IAsyncOperation[GattDeviceServicesResult](
                    self._requester.GetGattServicesAsync()
                ),
                return_type=GattDeviceServicesResult,
                loop=self.loop,
            )
            if services_result.Status == GattCommunicationStatus.Success:
                self.services = {s.Uuid.ToString(): s for s in services_result.Services}
            else:
                raise BleakDotNetTaskError("Could not get GATT services.")

            # TODO: Check if fetching failures...
            for service in services_result.Services:
                characteristics_result = await wrap_IAsyncOperation(
                    IAsyncOperation[GattCharacteristicsResult](
                        service.GetCharacteristicsAsync()
                    ),
                    return_type=GattCharacteristicsResult,
                    loop=self.loop,
                )
                if characteristics_result.Status != GattCommunicationStatus.Success:
                    raise BleakDotNetTaskError(
                        "Could not get GATT characteristics for {0}.".format(service)
                    )
                for characteristic in characteristics_result.Characteristics:
                    self.characteristics[
                        characteristic.Uuid.ToString()
                    ] = characteristic
                    descriptors_result = await wrap_IAsyncOperation(
                        IAsyncOperation[GattDescriptorsResult](
                            characteristic.GetDescriptorsAsync()
                        ),
                        return_type=GattDescriptorsResult,
                        loop=self.loop,
                    )
                    if descriptors_result.Status != GattCommunicationStatus.Success:
                        raise BleakDotNetTaskError(
                            "Could not get GATT descriptors for {0}.".format(
                                characteristic
                            )
                        )
                    for descriptor in list(descriptors_result.Descriptors):
                        self.descriptors[descriptor.Uuid.ToString()] = descriptor
                self.service_objects.append(BleakGATTServiceDotNet(service))

            # TODO: Could this be sped up?
            # await asyncio.gather(
            #     *[
            #         asyncio.ensure_future(self._get_chars(service), loop=self.loop)
            #         for service_uuid, service in self.services.items()
            #     ]
            # )
            self._services_resolved = True
            return self.services

    # I/O methods

    async def read_gatt_char(self, _uuid: str) -> bytearray:
        """Perform read operation on the specified characteristic.

        Args:
            _uuid (str or UUID): The uuid of the characteristics to read from.

        Returns:
            (bytearray) The read data.

        """
        characteristic = self.characteristics.get(str(_uuid))
        if not characteristic:
            raise BleakError("Characteristic {0} was not found!".format(_uuid))

        read_result = await wrap_IAsyncOperation(
            IAsyncOperation[GattReadResult](
                characteristic.ReadValueAsync(BluetoothCacheMode.Uncached)
            ),
            return_type=GattReadResult,
            loop=self.loop,
        )
        if read_result.Status == GattCommunicationStatus.Success:
            reader = DataReader.FromBuffer(IBuffer(read_result.Value))
            # TODO: Find better way of initializing this...
            output = Array[Byte]([0] * reader.UnconsumedBufferLength)
            reader.ReadBytes(output)
            value = bytearray(output)
            logger.debug("Read Characteristic {0} : {1}".format(_uuid, value))
        else:
            raise BleakError(
                "Could not read characteristic value for {0}: {1}".format(
                    characteristic.Uuid.ToString(), read_result.Status
                )
            )
        return value

    async def read_gatt_descriptor(self, _uuid: str) -> bytearray:
        """Perform read operation on the specified descriptor.

        Args:
            _uuid (str or UUID): The uuid of the descriptor to read from.

        Returns:
            (bytearray) The read data.

        """
        descriptor = self.descriptors.get(str(_uuid))
        if not descriptor:
            raise BleakError("Descriptor {0} was not found!".format(_uuid))

        read_result = await wrap_IAsyncOperation(
            IAsyncOperation[GattReadResult](
                descriptor.ReadValueAsync(BluetoothCacheMode.Uncached)
            ),
            return_type=GattReadResult,
            loop=self.loop,
        )
        if read_result.Status == GattCommunicationStatus.Success:
            reader = DataReader.FromBuffer(IBuffer(read_result.Value))
            output = Array[Byte]([0] * reader.UnconsumedBufferLength)
            reader.ReadBytes(output)
            value = bytearray(output)
            logger.debug("Read Descriptor {0} : {1}".format(_uuid, value))
        else:
            raise BleakError(
                "Could not read Descriptor value for {0}: {1}".format(
                    descriptor.Uuid.ToString(), read_result.Status
                )
            )

        return value

    async def write_gatt_char(
        self, _uuid: str, data: bytearray, response: bool = False
    ) -> Any:
        """Perform a write operation of the specified characteristic.

        Args:
            _uuid (str or UUID): The uuid of the characteristics to write to.
            data (bytes or bytearray): The data to send.
            response (bool): If write response is desired.

        """
        characteristic = self.characteristics.get(str(_uuid))
        if not characteristic:
            raise BleakError("Characteristic {0} was not found!".format(_uuid))

        writer = DataWriter()
        writer.WriteBytes(Array[Byte](data))
        if response:

            write_result = await wrap_IAsyncOperation(
                IAsyncOperation[GattWriteResult](
                    characteristic.WriteValueWithResultAsync(writer.DetachBuffer())
                ),
                return_type=GattWriteResult,
                loop=self.loop,
            )
            status = write_result.Status
        else:
            write_result = await wrap_IAsyncOperation(
                IAsyncOperation[GattCommunicationStatus](
                    characteristic.WriteValueAsync(writer.DetachBuffer())
                ),
                return_type=GattCommunicationStatus,
                loop=self.loop,
            )
            status = write_result
        if status == GattCommunicationStatus.Success:
            logger.debug("Write Characteristic {0} : {1}".format(_uuid, data))
        else:
            raise BleakError(
                "Could not write value {0} to characteristic {1}: {2}".format(
                    data, characteristic.Uuid.ToString(), write_result.Status
                )
            )

    async def write_gatt_descriptor(
        self, _uuid: str, data: bytearray, response: bool = False
    ) -> Any:
        """Perform a write operation of the specified descriptor.

        Args:
            _uuid (str or UUID): The uuid of the descriptor to write to.
            data (bytes or bytearray): The data to send.
            response (bool): If write response is desired.

        """
        descriptor = self.descriptors.get(str(_uuid))
        if not descriptor:
            raise BleakError("Descriptor {0} was not found!".format(_uuid))

        writer = DataWriter()
        writer.WriteBytes(Array[Byte](data))
        if response:

            write_result = await wrap_IAsyncOperation(
                IAsyncOperation[GattWriteResult](
                    descriptor.WriteValueWithResultAsync(writer.DetachBuffer())
                ),
                return_type=GattWriteResult,
                loop=self.loop,
            )
        else:
            write_result = await wrap_IAsyncOperation(
                IAsyncOperation[GattWriteResult](
                    descriptor.WriteValueAsync(writer.DetachBuffer())
                ),
                return_type=GattWriteResult,
                loop=self.loop,
            )
        if write_result.Status == GattCommunicationStatus.Success:
            logger.debug("Write Descriptor {0} : {1}".format(_uuid, data))
        else:
            raise BleakError(
                "Could not write value {0} to descriptor {1}: {2}".format(
                    data, descriptor.Uuid.ToString(), write_result.Status
                )
            )

    async def start_notify(
        self, _uuid: str, callback: Callable[[str, Any], Any], **kwargs
    ) -> None:
        """Activate notifications on a characteristic.

        Callbacks must accept two inputs. The first will be a uuid string
        object and the second will be a bytearray.

        .. code-block:: python

            def callback(sender, data):
                print(f"{sender}: {data}")
            client.start_notify(char_uuid, callback)

        Args:
            _uuid (str or UUID): The uuid of the characteristics to start notification on.
            callback (function): The function to be called on notification.

        """
        characteristic = self.characteristics.get(str(_uuid))

        if self._notification_callbacks.get(str(_uuid)):
            await self.stop_notify(_uuid)

        status = await self._start_notify(characteristic, callback)

        if status != GattCommunicationStatus.Success:
            raise BleakError(
                "Could not start notify on {0}: {1}".format(
                    characteristic.Uuid.ToString(), status
                )
            )

    async def _start_notify(self, characteristic, callback):

        if characteristic.CharacteristicProperties & GattCharacteristicProperties.Indicate:
            cccd = GattClientCharacteristicConfigurationDescriptorValue.Indicate
        elif characteristic.CharacteristicProperties & GattCharacteristicProperties.Notify:
            cccd = GattClientCharacteristicConfigurationDescriptorValue.Notify
        else:
            cccd = getattr(GattClientCharacteristicConfigurationDescriptorValue, 'None')

        status = await wrap_IAsyncOperation(
            IAsyncOperation[GattCommunicationStatus](
                characteristic.WriteClientCharacteristicConfigurationDescriptorAsync(cccd)
            ),
            return_type=GattCommunicationStatus,
            loop=self.loop,
        )
        if status == GattCommunicationStatus.Success:
            # Server has been informed of clients interest.
            try:
                # TODO: Enable adding multiple handlers!
                self._callbacks[characteristic.Uuid.ToString()] = TypedEventHandler[GattCharacteristic, GattValueChangedEventArgs](
                        _notification_wrapper(callback)
                )
                self._bridge.AddValueChangedCallback(characteristic, self._callbacks[characteristic.Uuid.ToString()])
            except Exception as e:
                # This usually happens when a device reports that it support indicate, but it actually doesn't.
                # TODO: Do not use Indicate? Return with Notify?
                return GattCommunicationStatus.AccessDenied
        return status

    async def stop_notify(self, _uuid: str) -> None:
        """Deactivate notification on a specified characteristic.

        Args:
            _uuid: The characteristic to stop notifying on.

        """
        characteristic = self.characteristics.get(str(_uuid))

        status = await wrap_IAsyncOperation(
            IAsyncOperation[GattCommunicationStatus](
                characteristic.WriteClientCharacteristicConfigurationDescriptorAsync(
                    getattr(GattClientCharacteristicConfigurationDescriptorValue, 'None')
                )
            ),
            return_type=GattCommunicationStatus,
            loop=self.loop,
        )

        if status != GattCommunicationStatus.Success:
            raise BleakError(
                "Could not start notify on {0}: {1}".format(
                    characteristic.Uuid.ToString(), status
                )
            )
        else:
            callback = self._callbacks.pop(characteristic.Uuid.ToString())
            self._bridge.RemoveValueChangedCallback(characteristic, callback)


def _notification_wrapper(func: Callable):
    @wraps(func)
    def dotnet_notification_parser(sender: Any, args: Any):
        # Return only the UUID string representation as sender.
        # Also do a conversion from System.Bytes[] to bytearray.
        reader = DataReader.FromBuffer(args.CharacteristicValue)
        output = Array[Byte]([0] * reader.UnconsumedBufferLength)
        reader.ReadBytes(output)

        return func(sender.Uuid.ToString(), bytearray(output))

    return dotnet_notification_parser
