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
        self.cal_constants = {
            pt.get_pt_id(): pt.logger.get_latest_set_of_cals(pt.get_num_pts())
            for pt in pts
        }
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

        for pt in self.pts:
            constants = self.cal_constants[pt.get_pt_id()]
            for index in pt.selected_sensor_indices:
                row_key = f"{pt.get_pt_id()}-PT-{index}"
                slope, intercept = constants[index]
                table.add_row(
                    f"{pt.get_pt_name()} PT {index}",
                    f"{slope:.8f}",
                    f"{intercept:.8f}",
                    key=row_key,
                )

    def action_test_reading(self):
        """Read from serial, and calculate the resultant pressure using the calibration factors saved"""
        try:
            table = self.query_one("#Test-Calibration-Table", DataTable)
            self.take_and_calculate_readings(table)
        except NoMatches:
            pass

    @work(thread=True, exit_on_error=True)
    async def take_and_calculate_readings(self, table: DataTable):
        for pt in self.pts:
            raw_readings = pt.read()
            constants = self.cal_constants[pt.get_pt_id()]
            for index, raw_reading in zip(pt.selected_sensor_indices, raw_readings):
                row_key = f"{pt.get_pt_id()}-PT-{index}"
                slope, intercept = constants[index]
                reading = slope * raw_reading + intercept
                table.update_cell(
                    row_key=row_key,
                    column_key="Pressure",
                    value=f"{reading:.8f}",
                )
                table.update_cell(
                    row_key=row_key,
                    column_key="Raw pressure",
                    value=f"{raw_reading:.8f}",
                )

    # plan: add a button here that can be clicked when we want to test calibrations
    # it will: (1) load calibrations from file
    # (2) reset buffer and take a single reading from serial
    # (3) display, in a table, for each PT: (a) the results of the calibrated values (b) the m and c values
    # (4) button can then be clicked again if we want to test the values
