from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label, ProgressBar, DataTable
from textual.containers import HorizontalGroup, VerticalGroup, Container, Middle, Center
from textual.validation import Number
from textual.reactive import reactive
from textual.css.query import NoMatches
from textual.message import Message
from textual.widget import Widget
from textual.timer import Timer
from textual.worker import get_current_worker

from serial_reader import serial_reader
from logger import logger

RAW_DATA_LV_FILENAME = "raw_readings_lv.csv"
AVG_DATA_LV_FILENAME = "avg_readings_lv.csv"


class CalculateLinearRegressionAction(Message):
    def __init__(self):
        super().__init__()


class TriggerCalibrationMessageAction(Message):
    def __init__(self):
        super().__init__()


class AutoCalCli(App):
    """A textual app to get user input for linear regression calculations"""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+g", "calibrate", "Calibrate PTs"),
    ]

    def __init__(
        self,
        baud_rate: int,
        num_readings_per_pressure: int,
        pt_configs: list[dict[str, str | int]],
        hv: str,
        lv: str,
    ):
        # dynamically load the PTs that you have to read from
        self.pts = []
        for config in pt_configs:
            assert isinstance(port := config.get("port", None), str)
            assert isinstance(pt_count := config.get("pt_count", None), int)
            assert isinstance(name := config.get("name", None), str)

            self.pts.append(
                serial_reader.SerialReader(
                    serial_port=port,
                    baud_rate=baud_rate,
                    num_sensors=pt_count,
                    num_readings_per_pt=num_readings_per_pressure,
                    name=name,
                    logger=logger.Logger(
                        raw_data_filename=RAW_DATA_LV_FILENAME,
                        avg_data_filename=AVG_DATA_LV_FILENAME,
                    ),
                )
            )

        self.num_readings_per_pt = num_readings_per_pressure
        self.hv = hv
        self.lv = lv
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create header and footer"""
        yield Header()
        yield Footer()
        yield FullCalibrationDisplay(
            self.pts, self.num_readings_per_pt, self.hv, self.lv
        )

    def _post_calibration_message(self) -> None:
        """Calculate the linear regression for all PTs"""
        for calibration_display in self.query(PreviousCalculationDisplay):
            calibration_display.post_message(CalculateLinearRegressionAction())

    def action_calibrate(self) -> None:
        """Tell the system to calculate the linear regression"""
        self._post_calibration_message()

    def on_trigger_calibration_message_action(
        self, message: TriggerCalibrationMessageAction
    ) -> None:
        self._post_calibration_message()


class AverageRawReadingUpdated(Message):
    def __init__(self, pressure: float, raw_readings: list[float], pt_id: str) -> None:
        self.pressure = pressure
        self.raw_readings = raw_readings
        self.pt_id = pt_id
        super().__init__()


class TableRowUpdated(Message):
    def __init__(self, pressure: float, raw_readings: list[float], pt_id: str) -> None:
        self.pressure = pressure
        self.raw_readings = raw_readings
        self.pt_id = pt_id
        super().__init__()


class FullCalibrationDisplay(HorizontalGroup):
    """The main container for displaying the current readings and the previously calculated readings"""

    # dynamically generate the CSS so that the tables can have ample space
    CSS = """
        #previous-display {
            border: solid orange;
            layout: grid;
            grid-size: 2 1;
        }
    """

    def __init__(
        self,
        pts: list[serial_reader.SerialReader],
        num_readings_per_pressure: int,
        hv: str,
        lv: str,
    ):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.pts = pts
        self.total_num_pts = sum([i.get_num_pts() for i in pts])
        self.hv = hv
        self.lv = lv
        super().__init__()

    # current set of readings + current set of commands
    def compose(self) -> ComposeResult:
        with Container(id="main-app-container"):
            yield CurrentCalibrationDisplay(
                self.num_readings_per_pressure, self.pts, self.hv, self.lv
            )
            with Container(id="previous-display"):
                for reader in self.pts:
                    yield PreviousCalculationDisplay(reader, self.hv, self.lv)

    def on_average_raw_reading_updated(self, message: AverageRawReadingUpdated) -> None:
        print("got the message here", message)
        for prev_display in self.query(PreviousCalculationDisplay):
            prev_display.post_message(
                TableRowUpdated(message.pressure, message.raw_readings, message.pt_id)
            )

    def on_mount(self) -> None:
        prev_display_container = self.query_one("#previous-display", Container)
        prev_display_container.styles.border = ("solid", "orange")

        prev_display_container.styles.grid_size_columns = 2
        prev_display_container.styles.grid_size_rows = 1

        # allocate space on the number of pts that each port has

        container_split = ""
        for pt in self.pts:
            container_split += f" {int( (pt.get_num_pts() + 1) / (self.total_num_pts + len(self.pts) ) * 100)}%"

        print("the style is ", container_split.strip())
        prev_display_container.styles.grid_columns = container_split.strip()

        prev_display_container.styles.layout = "grid"


class PressureUpdated(Message):
    def __init__(self, pressure: float) -> None:
        self.pressure = pressure
        super().__init__()


class CurrentCalibrationDisplay(VerticalGroup):
    """Display the current set of readings + the command prompt"""

    current_pressure: reactive[float] = reactive(-1)

    def __init__(
        self,
        num_readings_per_pressure: int,
        pts: list[serial_reader.SerialReader],
        hv: str,
        lv: str,
    ):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.pts = pts
        self.hv = hv
        self.lv = lv
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-container"):
            yield CurrentCalibrationUserInputWidget().data_bind()
            yield CurrentCalibrationProgressIndicator(
                self.num_readings_per_pressure, self.pts, self.hv, self.lv
            ).data_bind(CurrentCalibrationDisplay.current_pressure)

    def on_pressure_updated(self, message: PressureUpdated) -> None:
        """Handle pressure updates from child widgets"""
        self.current_pressure = message.pressure

        # reset the progress bar as well
        try:
            for progress_bar in self.query(ProgressBar):
                progress_bar.update(progress=0)
        except NoMatches:
            pass


class CurrentCalibrationProgressIndicator(Widget):
    current_pressure: reactive[float] = reactive(-1)
    raw_reading: reactive[float] = reactive(-1)

    progress_timer: Timer
    is_first_load = True

    def __init__(
        self,
        num_readings_per_pressure: int,
        pts: list[serial_reader.SerialReader],
        hv: str,
        lv: str,
    ):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.pts = pts
        self.hv = hv
        self.lv = lv
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-progress-indicator"):
            yield Label(
                f"Reading pressure... {self.current_pressure}", id="pressure-display"
            )
            yield Label("", id="raw-reading")
            # render a progress bar for each set of PTs
            with Middle(id="progress-bar-container"):
                for pt_set in self.pts:
                    with Container():
                        with Center():
                            yield Label(f"{pt_set.get_pt_name()} pts")
                        with Center():
                            yield ProgressBar(
                                total=self.num_readings_per_pressure,
                                show_eta=False,
                                show_percentage=False,
                                id=f"{pt_set.get_pt_id()}-progress",
                            )

    def watch_current_pressure(self, pressure: float) -> None:
        """Update the label when pressure changes"""
        try:
            label = self.query_one("#pressure-display", Label)
            label.update(f"Reading pressure... {pressure if pressure >= 0 else ''}")
            self.current_pressure = pressure

            if not self.is_first_load:
                for reader in self.pts:
                    self.take_readings_from_serial(reader, self.current_pressure)

            else:
                self.is_first_load = False

        except NoMatches:
            pass

    @work(thread=True, exit_on_error=True)
    async def take_readings_from_serial(
        self, reader: serial_reader.SerialReader, current_pressure: float
    ) -> None:
        """reader to read simultaneously from each serial port"""
        worker = get_current_worker()
        if worker.is_cancelled:
            raise Exception("Worker errored out, aborting calibration...")

        for i in range(self.num_readings_per_pressure):
            reader.read_from_serial(
                is_first_reading=(i == 0), current_pressure=current_pressure
            )
            try:
                self.query_one(f"#{reader.get_pt_id()}-progress", ProgressBar).advance(
                    1
                )
            except NoMatches:
                pass

        if reader.ready_for_avg():
            self.post_message(
                AverageRawReadingUpdated(
                    self.current_pressure,
                    reader.calculate_avg(self.current_pressure),
                    reader.get_pt_id(),
                )
            )

        return

    def watch_raw_reading(self, new_reading: float) -> None:
        """Update the screen when a raw reading comes in from serial"""
        try:
            label = self.query_one("#raw-reading", Label)
            label.update(f"{f'Raw reading: {new_reading}' if new_reading >= 0 else ''}")

        except NoMatches:
            pass

    def on_mount(self) -> None:
        """set the progress on all bars to 0"""
        for progress_bar in self.query(ProgressBar):
            progress_bar.update(progress=0)


class CurrentCalibrationUserInputWidget(VerticalGroup):
    """The widget which accepts user input"""

    BINDINGS = [
        ("escape", "blur", "unfocus input"),
        ("ctrl+g", "calibrate_message", "calibrate PTs"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-input-container"):
            yield Label("Current pressure", id="current-pressure-label")
            yield Input(
                id="current-pressure-input",
                validate_on=["submitted"],
                validators=[Number()],
            )
            yield Label("", id="error-message")

    @on(Input.Submitted)
    def accept_user_input(self, event: Input.Submitted):
        input_widget = self.query_one("#current-pressure-input", Input)
        if event.validation_result:
            if event.validation_result.is_valid:
                self.set_error_label("")
                try:
                    pressure_value = float(input_widget.value)
                    self.post_message(PressureUpdated(pressure_value))
                except ValueError:
                    self.set_error_label("Invalid number format!")
            else:
                self.set_error_label("Pressure should be a number!")

        input_widget.value = ""

    def set_error_label(self, error_value: str) -> None:
        error_label = self.query_one("#error-message", Label)
        error_label.update(error_value)

    def on_mount(self) -> None:
        self.call_after_refresh(lambda: self.screen.set_focus(None))

    def action_blur(self) -> None:
        self.screen.set_focus(None)
        self.set_error_label("")
        input_widget = self.query_one("#current-pressure-input", Input)
        input_widget.remove_class("-invalid")

    def action_calibrate_message(self) -> None:
        self.post_message(TriggerCalibrationMessageAction())


class PreviousCalculationDisplay(VerticalGroup):
    def __init__(self, reader: serial_reader.SerialReader, hv: str, lv: str) -> None:
        self.reader = reader
        self.hv = hv
        self.lv = lv
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id=f"{self.reader.get_pt_id()}-previous-display"):
            yield Label(
                f"Previous readings for {self.reader.get_pt_name()} PTs",
                id=f"{self.reader.get_pt_id()}-data-table-label",
            )
            yield DataTable(id=f"{self.reader.get_pt_id()}-data-table")

    def on_mount(self) -> None:
        table = self.query_one(f"#{self.reader.get_pt_id()}-data-table", DataTable)

        # create an additional column for each PT there is
        pt_columns = [f"PT {i}" for i in range(self.reader.get_num_pts())]
        table.add_column("PSI", key="Pressure")
        for pt in pt_columns:
            table.add_column(pt, key=pt)

    def on_table_row_updated(self, message: TableRowUpdated) -> None:
        # only handle the message if it is meant for this table
        print("message received: ", message)

        if message.pt_id != self.reader.get_pt_id():
            return

        table = self.query_one(f"#{self.reader.get_pt_id()}-data-table", DataTable)

        # only add rows to the table if the values are valid
        if message.pressure >= 0 and message.pressure >= 0:
            table.add_row(message.pressure, *message.raw_readings)

    def on_calculate_linear_regression_action(
        self, message: CalculateLinearRegressionAction
    ) -> None:
        try:
            table = self.query_one(f"#{self.reader.get_pt_id()}-data-table", DataTable)
            self.query_one(
                f"#{self.reader.get_pt_id()}-data-table-label", Label
            ).update(f"Calibration factors for {self.reader.get_pt_name()} PTs")
        except NoMatches:
            return

        table.clear()

        # remove the old columns
        table.remove_column("Pressure")
        pt_columns = [f"PT {i}" for i in range(self.reader.get_num_pts())]
        for pt in pt_columns:
            table.remove_column(pt)

        # add a calibration column to the start
        table.add_column("Calibration Values", key="values")
        table.add_columns(*pt_columns)

        lrs = self.reader.get_all_linear_regressions()

        # add the m values
        slopes = [val[0] for val in lrs.values()]
        table.add_row("m", *slopes)

        intercepts = [val[1] for val in lrs.values()]
        table.add_row("c", *intercepts)
