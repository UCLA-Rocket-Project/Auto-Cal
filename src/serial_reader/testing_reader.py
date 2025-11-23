import struct
from threading import Lock
from typing import Callable, cast

from serial import Serial

from logger.logger import Logger
from serial_reader.serial_reader import SerialReader


class TestingReader(SerialReader):
    def __init__(
        self,
        serial: Serial,
        serial_lock: Lock,
        num_sensors: int,
        name: str,
        logger: Logger,
        decode_fn: Callable[[bytes], list[float]],
        stop_sequence: bytes,
        expected_payload_length: int,
    ):
        super().__init__(
            serial=serial,
            serial_lock=serial_lock,
            num_sensors=num_sensors,
            name=name,
            logger=logger,
            decode_fn=decode_fn,
            stop_sequence=stop_sequence,
            expected_payload_length=expected_payload_length,
        )

    def read(self) -> list[float]:
        line = self.read_raw(reset_input=True)

        readings = None
        try:
            readings = self.decode_fn(line)
        except struct.error as e:
            assert 0, f"Error: {str(e)}. Struct had length {len(line)}"
        except UnicodeDecodeError as e:
            assert 0, f"Unable to decode struct"

        # if this passes, this will be the raw voltages read
        return cast(list[float], readings)
