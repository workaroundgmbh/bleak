# -*- coding: utf-8 -*-
import platform
import re
import os
from typing import Optional

from dbus_fast.auth import AuthExternal
from dbus_fast.constants import MessageType
from dbus_fast.message import Message

from ...exc import BleakDBusError, BleakError


def assert_reply(reply: Message) -> None:
    """Checks that a D-Bus message is a valid reply.

    Raises:
        BleakDBusError: if the message type is ``MessageType.ERROR``
        AssertionError: if the message type is not ``MessageType.METHOD_RETURN``
    """
    if reply.message_type == MessageType.ERROR:
        raise BleakDBusError(reply.error_name, reply.body)
    assert reply.message_type == MessageType.METHOD_RETURN


def extract_service_handle_from_path(path: str) -> int:
    try:
        return int(path[-4:], 16)
    except Exception as e:
        raise BleakError(f"Could not parse service handle from path: {path}") from e


def bdaddr_from_device_path(device_path: str) -> str:
    """
    Scrape the Bluetooth address from a D-Bus device path.

    Args:
        device_path: The D-Bus object path of the device.

    Returns:
        A Bluetooth address as a string.
    """
    return ":".join(device_path[-17:].split("_"))


def device_path_from_characteristic_path(characteristic_path: str) -> str:
    """
    Scrape the device path from a D-Bus characteristic path.

    Args:
        characteristic_path: The D-Bus object path of the characteristic.

    Returns:
        A D-Bus object path of the device.
    """
    # /org/bluez/hci1/dev_FA_23_9D_AA_45_46/service000c/char000d
    return characteristic_path[:37]


def get_dbus_authenticator() -> Optional[AuthExternal]:
    uid = None
    try:
        uid = int(os.environ.get("BLEAK_DBUS_AUTH_UID", ""))
    except ValueError:
        pass

    auth = None
    if uid is not None:
        auth = AuthExternal(uid=uid)

    return auth


def is_running_on_gateway() -> bool:
    """
    Determines if the code is running on a gateway device.

    Proglove Gateways have a hostname that starts with "gateway-"
    and has 5 to 6 decimal digits after the hyphen.

    Returns:
        True if running on a gateway device, False otherwise.
    """
    hostname = platform.node().lower()
    cpu_arch = platform.machine().lower()
    return re.match(r"^gateway-\d{5,6}$", hostname) is not None and cpu_arch.startswith(
        "arm"
    )
