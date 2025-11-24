import threading
from typing import Callable

from serial import Serial

from logger import logger


class SerialReader:
    def __init__(
        self,
        port: str,
        baudrate: int,
        serial_lock: threading.Lock,
        num_sensors: int,
        name: str,
        logger: logger.Logger,
        decode_fn: Callable[[bytes], list[float]],
        stop_sequence: bytes,
        expected_payload_length: int,
    ):
        self.num_sensors = num_sensors
        self.serial_lock = serial_lock
        self.name = name
        self.logger = logger
        self.decode_fn = decode_fn
        self.stop_sequence = stop_sequence
        self.expected_payload_length = expected_payload_length
        self.port = port
        self.baudrate = baudrate

    def read_raw(self, reset_input: bool) -> bytes:
        """Implements the pure reading function"""
        with self.serial_lock:
            with Serial(self.port, self.baudrate, timeout=0.5) as ser:
                line = b""
                while (l := len(line)) < self.expected_payload_length:
                    line += ser.read(self.expected_payload_length - l)

            return line

    def get_pt_name(self) -> str:
        return self.name

    def get_num_pts(self) -> int:
        return self.num_sensors
