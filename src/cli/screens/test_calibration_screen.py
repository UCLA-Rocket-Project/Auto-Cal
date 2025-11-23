from textual import work
from textual.binding import Binding
from textual.containers import Container
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label

from serial_reader.testing_reader import TestingReader


class TestCalibrationScreen(Screen):

    BINDINGS = [
        Binding("ctrl+g", "calibrate", "Calibrate PTs", show=False),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+t", "test_calibrations", "Test Calibrated Values", show=False),
        Binding("ctrl+w", "calibrate", "Switch To Calibration Mode", show=True),
        Binding("ctrl+a", "test_reading", "Read with calibration factor", show=True),
    ]

    def __init__(self, pts: list[TestingReader]):
        self.pts = pts
        self.cal_constants = pts[0].logger.get_latest_set_of_cals(pts[0].get_num_pts())
        super().__init__()

    def compose(self):
        yield Header()
        yield Footer()
        with Container(id="Testing-Container"):
            yield Label("Calibration Testing Screen")
            yield DataTable(id="Test-Calibration-Table")

    def on_mount(self) -> None:
        table = self.query_one("#Test-Calibration-Table", DataTable)

        table.add_column("PT Name", key="PT Name")
        table.add_column("m", key="Gradient")
        table.add_column("c", key="Offset")

        table.add_column("Raw pressure reading", key="Raw pressure")
        table.add_column("Calibrated Pressure Reading", key="Pressure")

        pt_rows = [f"PT {i}" for i in range(self.pts[0].get_num_pts())]
        for constants, row_key in zip(self.cal_constants, pt_rows):
            table.add_row(row_key, constants[0], constants[1], key=row_key)

    def action_test_reading(self):
        """Read from serial, and calculate the resultant pressure using the calibration factors saved"""
        try:
            table = self.query_one("#Test-Calibration-Table", DataTable)
            self.take_and_calculate_readings(table)
        except NoMatches:
            pass

    @work(thread=True, exit_on_error=True)
    async def take_and_calculate_readings(self, table: DataTable):
        raw_readings = self.pts[0].read()

        assert len(raw_readings) == len(
            self.cal_constants
        ), f"Lengths of readings {len(raw_readings)} do not match up with calibration constants {len(self.cal_constants)}"
        for i in range(len(raw_readings)):
            row_key = f"PT {i}"
            reading = float(self.cal_constants[i][0]) * raw_readings[i] + float(
                self.cal_constants[i][1]
            )
            table.update_cell(
                row_key=row_key,
                column_key="Pressure",
                value=reading,
            )
            table.update_cell(
                row_key=row_key, column_key="Raw pressure", value=raw_readings[i]
            )

    # plan: add a button here that can be clicked when we want to test calibrations
    # it will: (1) load calibrations from file
    # (2) reset buffer and take a single reading from serial
    # (3) display, in a table, for each PT: (a) the results of the calibrated values (b) the m and c values
    # (4) button can then be clicked again if we want to test the values
