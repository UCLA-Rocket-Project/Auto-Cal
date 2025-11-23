from serial import Serial
import threading, time
from logger import logger
from typing import Callable


class SerialReader:
    def __init__(
        self,
        serial: Serial,
        serial_lock: threading.Lock,
        num_sensors: int,
        name: str,
        logger: logger.Logger,
        decode_fn: Callable[[bytes], list[float]],
        stop_sequence: bytes,
        expected_payload_length: int,
    ):
        self.serial = serial
        self.num_sensors = num_sensors
        self.serial_lock = serial_lock
        self.name = name
        self.logger = logger
        self.decode_fn = decode_fn
        self.stop_sequence = stop_sequence
        self.expected_payload_length = expected_payload_length

    def _sync(self) -> None:
        self.serial.read_until(self.stop_sequence)

    def read_raw(self, reset_input: bool) -> bytes:
        """Implements the pure reading function"""
        with self.serial_lock:
            if reset_input:
                self.serial.reset_input_buffer()
                # let the buffer fill up again
                time.sleep(1)
                self._sync()

            line = b""
            while (l := len(line)) < self.expected_payload_length:
                line += self.serial.read(self.expected_payload_length - l)

            return line

    def __del__(self):
        self.serial.close()
