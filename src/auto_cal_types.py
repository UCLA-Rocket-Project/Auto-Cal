from threading import Lock
from typing import Callable, TypedDict, Union

from serial import Serial

from logger.logger import Logger


class PTConfigs(TypedDict):
    port: str
    pt_count: int
    name: str
    serial: Serial | None
    serial_lock: Union[Lock, None]
    logger: Logger
    stop_sequence: bytes
    decode_fn: Callable[[bytes], list[float]]
    expected_payload_length: int


class ConfigFields(TypedDict):
    baud_rate: int
    pt_configs: list[PTConfigs]
    num_readings_per_pt: int
