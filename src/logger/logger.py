import logging, sys, time


class Logger:
    def __init__(self, raw_data_filename: str, avg_data_filename: str):
        """raw data records all the readings, avg data records the averaged value"""
        # try to create the new file if it does not yet exist
        try:
            file = open(raw_data_filename, "w")
            file.close()
        except FileExistsError:
            pass

        try:
            file = open(avg_data_filename, "w")
            file.close()
        except FileExistsError:
            pass

        self.raw_data_file = open(raw_data_filename, "a")
        self.avg_data_file = open(avg_data_filename, "a")

    def _get_time(self) -> int:
        return int(time.time_ns() / 1_000_000)

    def log_raw_data(self, text: str):
        self.raw_data_file.write(f"{self._get_time()}, {text}\n")
        self.raw_data_file.flush()

    def log_avg_data(self, text: str):
        self.avg_data_file.write(f"{self._get_time()}, {text}\n")
        self.avg_data_file.flush()


if __name__ == "__main__":
    log = Logger("../../test.csv", "../../test2.csv")
    log.log_avg_data("sheesh")
