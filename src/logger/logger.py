import time, os


class Logger:
    def __init__(
        self,
        raw_data_filename: str,
        avg_data_filename: str,
        stored_calibration_filename: str,
    ):
        """raw data records all the readings, avg data records the averaged value"""
        self.stored_cals_filename = stored_calibration_filename

        # try to create the new file if it does not yet exist
        try:
            file = open(raw_data_filename, "x")
            file.close()
        except FileExistsError:
            pass

        try:
            file = open(avg_data_filename, "x")
            file.close()
        except FileExistsError:
            pass

        try:
            file = open(stored_calibration_filename, "x")
            file.close()
        except FileExistsError:
            pass

        self.raw_data_file = open(raw_data_filename, "a")
        self.avg_data_file = open(avg_data_filename, "a")
        self.stored_cals_file = open(stored_calibration_filename, "a")

    def __del__(self):
        self.raw_data_file.close()
        self.avg_data_file.close()
        self.stored_cals_file.close()

    def _get_time(self) -> int:
        return int(time.time_ns() / 1_000_000)

    def log_raw_data(self, text: str):
        self.raw_data_file.write(f"{self._get_time()},{text}\n")
        self.raw_data_file.flush()

    def log_avg_data(self, text: str):
        self.avg_data_file.write(f"{self._get_time()},{text}\n")
        self.avg_data_file.flush()

    def log_cals(self, text: str):
        self.stored_cals_file.write(f"{self._get_time()},{text}\n")
        self.stored_cals_file.flush()

    def get_latest_set_of_cals(self, num_sensors: int) -> list[tuple[float, float]]:
        self.stored_cals_file.flush()
        self.stored_cals_file.close()

        x_line = None
        y_line = None

        with open(self.stored_cals_filename, "rb") as file:
            # read the last 2 lines for calibrations
            # start by finding the last line
            try:
                # -2 first to skip the newline that is at the back of the last line
                file.seek(-2, os.SEEK_END)

                # coeffs are written in 2 lines, first x then y

                # this gets the last line
                while file.read(1) != b"\n":
                    file.seek(-2, os.SEEK_CUR)

                file.seek(-2, os.SEEK_CUR)
                # this gets the second last line
                while file.read(1) != b"\n":
                    file.seek(-2, os.SEEK_CUR)

            except OSError:
                file.seek(0)

            x_line = file.readline().decode()
            y_line = file.readline().decode()

        if not x_line or not y_line:
            raise Exception("Cannot read calibration values")

        # parse the calibration lines
        x_vals = x_line[:-1].split(",")[2:]
        y_vals = y_line[:-1].split(",")[2:]

        assert (
            len(x_vals) == len(y_vals)
            and f"Number calculated coeffs does not match. Number of m_vals {x_vals} | Number of c_vals {y_vals}"
        )

        assert (
            len(x_vals) == num_sensors
            and f"Number of sensors does not match the number of values obtained. Num sensors {num_sensors} | Num calibrated values {x_vals}"
        )

        self.stored_cals_file = open(self.stored_cals_filename, "a")

        return [(float(m), float(c)) for m, c in zip(x_vals, y_vals)]


if __name__ == "__main__":
    log = Logger("../../test.csv", "../../test2.csv", "outcals.csv")
    log.log_avg_data("sheesh")
