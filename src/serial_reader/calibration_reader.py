import struct
from threading import Lock
from typing import Callable

import numpy as np

from cal import cal
from logger.logger import Logger
from serial_reader.serial_reader import SerialReader


class CalibrationReader(SerialReader):
    def __init__(
        self,
        port: str,
        baudrate: int,
        serial_lock: Lock,
        num_sensors: int,
        name: str,
        logger: Logger,
        decode_fn: Callable[[bytes], list[float]],
        stop_sequence: bytes,
        expected_payload_length: int,
        num_readings_per_pt: int,
    ):
        super().__init__(
            port=port,
            baudrate=baudrate,
            serial_lock=serial_lock,
            num_sensors=num_sensors,
            name=name,
            logger=logger,
            decode_fn=decode_fn,
            stop_sequence=stop_sequence,
            expected_payload_length=expected_payload_length,
        )

        self.num_readings_per_pt = num_readings_per_pt
        self.all_avgs = {i: [] for i in range(num_sensors)}
        self.readings = {i: [] for i in range(num_sensors)}
        # id is different from name because ID must not have spaces
        self.id = "-".join(name.split(" "))

    def read_from_serial(self, is_first_reading: bool, current_pressure: float) -> None:
        """take a reading from serial, and place it into the readings dict"""
        # clear the current readings first
        # for the first reading of the set, clear the buffer and the first potentially incomplete line
        if is_first_reading:
            self.read_raw(reset_input=True)

        readings = None
        # try to take 10 differnt set of readings to get one set of accurate readings
        # NOTE: This function is potentially problematic, this might be the cause of errors
        for i in range(self.num_readings_per_pt):
            line = self.read_raw(reset_input=False)

            # skip this set of readings if theere are not enough bytes
            try:
                line_readings = self.decode_fn(line)
                if len(line_readings) == self.num_sensors:
                    readings = line_readings
                    # log the raw readings to the raw data file
                    self.logger.log_raw_data(
                        f"""{current_pressure},{",".join([f"{reading:.2f}" for reading in line_readings])}"""
                    )
                    break
            # let the loop try for a few times before exiting
            except struct.error:
                pass
            except UnicodeDecodeError:
                pass

        if not readings:
            raise Exception(
                f"None of the 10 readings gave the desired set of values. Aborting..."
            )

        if not readings:
            raise ValueError(
                f"Expected {self.num_sensors} readings, but received {len(readings) if readings else readings} | readings: {readings}"
            )

        # add the reading to the dict
        for pt_no, reading in enumerate(readings):
            self.readings[pt_no].append(np.float64(reading))

    def calculate_avg(self, current_pressure: float) -> list[float]:
        """calculate the average reading for the current set of values and clear the reading history"""
        avg_readings = []
        for pt_no, readings in self.readings.items():
            avg_for_pt = np.mean(np.array(readings)).item()
            avg_readings.append(avg_for_pt)
            self.all_avgs[pt_no].append((current_pressure, avg_for_pt))

            self.readings[pt_no] = []

        # log the average readings as well
        self.logger.log_avg_data(
            f"""{current_pressure},{",".join([f"{val:.2f}" for val in avg_readings])}"""
        )

        return avg_readings

    def ready_for_avg(self) -> bool:
        """crudely check for"""
        if len(self.readings) <= 0:
            raise Exception("No readings recorded for avg calculation")

        for reding_set in self.readings.values():
            if len(reding_set) != self.num_readings_per_pt:
                raise Exception(
                    f"Expected {self.num_readings_per_pt} readings, but only got {len(reding_set)} readings. Reading set: {self.readings}"
                )

        return True

    def get_all_linear_regressions(self) -> dict[int, tuple[float, float]]:
        """returns data in format pt: (m, c)"""
        linear_regressions = {}
        for pt, pressure_value_pair in self.all_avgs.items():
            pressures = []
            avg_readings = []
            for pressure, avg_reading in pressure_value_pair:
                pressures.append(pressure)
                avg_readings.append(avg_reading)

            linear_regressions[pt] = cal.calculate_linear_regression(
                avg_readings, pressures
            )

        # log the calibrated values into a file
        self.logger.log_cals(
            f"""x,{",".join([f"{x[0]}" for x in linear_regressions.values()])}"""
        )
        self.logger.log_cals(
            f"""y,{",".join([f"{x[1]}" for x in linear_regressions.values()])}"""
        )

        return linear_regressions

    def get_pt_id(self) -> str:
        return self.id
