from serial import Serial
import numpy as np
import threading, time
from cal import cal
import struct
from logger import logger


class SerialReader:
    def __init__(
        self,
        serial_port: str,
        baud_rate: int,
        num_sensors: int,
        num_readings_per_pt: int,
        name: str,
        logger: logger.Logger,
        timeout: int = 2,
    ):
        self.serial = Serial(serial_port, baudrate=baud_rate, timeout=timeout)
        self.readings = {i: [] for i in range(num_sensors)}
        self.num_sensors = num_sensors
        self.num_readings_per_pt = num_readings_per_pt
        self.serial_lock = threading.Lock()
        self.all_avgs = {i: [] for i in range(num_sensors)}
        self.name = name
        # id is different from name because ID must not have spaces
        self.id = "-".join(name.split(" "))

        self.logger = logger

    def __del__(self):
        self.serial.close()

    def read_and_return(self) -> list[float]:
        with self.serial_lock:
            self.serial.reset_input_buffer()

            # let the buffer fill up again
            time.sleep(1)
            self.serial.read_until(b"\r\n")

            line = self.serial.read_until(b"\r\n").rstrip(b"\r\n")

            readings = None
            try:
                readings = struct.unpack(f"{self.num_sensors}f", line)
            except struct.error as e:
                assert 0, f"Error unpacking struct, {len(line)} | Error: {str(e)}"
            except UnicodeDecodeError as e:
                assert 0, f"Unable to decode struct"

            # if this passes, this will be the raw voltages read
            return list(readings)

    def read_from_serial(self, is_first_reading: bool, current_pressure: float) -> None:
        """take a reading from serial, and place it into the readings dict"""
        # clear the current readings first
        with self.serial_lock:
            # for the first reading of the set, clear the buffer and the first potentially incomplete line
            if is_first_reading:
                self.serial.reset_input_buffer()

            readings = None
            try:
                # try to take 10 differnt set of readings to get one set of accurate readings
                for i in range(self.num_readings_per_pt):
                    line = self.serial.read_until(b"\r\n").rstrip(b"\r\n")

                    # skip this set of readings if theere are not enough bytes
                    try:
                        line_readings = struct.unpack(f"{self.num_sensors}f", line)
                        if len(line_readings) == self.num_sensors:
                            readings = line_readings
                            # log the raw readings to the raw data file
                            self.logger.log_raw_data(
                                f"""{current_pressure},{",".join([f"{reading:.2f}" for reading in line_readings])}"""
                            )
                            break
                    except struct.error:
                        pass

                    # increasing wait time if the readings are still not coming in properly
                    time.sleep(0.3 * (i + 1))

                if not readings:
                    raise Exception(
                        f"None of the 10 readings gave the desired set of values. Aborting..."
                    )

            except UnicodeDecodeError:
                print("Error decoding current sequence, continuing...")
                return

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
                pressures, avg_readings
            )

        # log the calibrated values into a file
        self.logger.log_cals(
            f"""x,{",".join([f"{x[0]}" for x in linear_regressions.values()])}"""
        )
        self.logger.log_cals(
            f"""y,{",".join([f"{x[1]}" for x in linear_regressions.values()])}"""
        )

        return linear_regressions

    def get_pt_name(self) -> str:
        return self.name

    def get_num_pts(self) -> int:
        return self.num_sensors

    def get_pt_id(self) -> str:
        return self.id
