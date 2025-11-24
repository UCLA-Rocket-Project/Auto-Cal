from threading import Lock
from typing import cast

from textual.app import App

from auto_cal_types import PTConfigs
from cli.screens import calibration_screen, test_calibration_screen
from serial_reader.calibration_reader import CalibrationReader
from serial_reader.testing_reader import TestingReader


class AutoCalCli(App):
    """A textual app to get user input for linear regression calculations"""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+t", "test_calibrations", "Test Calibratied Values"),
        ("ctrl+w", "calibrate", "Calibrate"),
    ]

    def __init__(
        self,
        pt_configs: list[PTConfigs],
        baudrate: int,
        num_readings_per_pressure: int,
        hv: str,
        lv: str,
    ):
        # dynamically load the PTs that you have to read from
        self.calibration_readers = [
            CalibrationReader(
                port=pt["port"],
                baudrate=baudrate,
                serial_lock=cast(Lock, pt["serial_lock"]),
                num_sensors=pt["pt_count"],
                name=pt["name"],
                logger=pt["logger"],
                decode_fn=pt["decode_fn"],
                stop_sequence=pt["stop_sequence"],
                expected_payload_length=pt["expected_payload_length"],
                num_readings_per_pt=num_readings_per_pressure,
            )
            for pt in pt_configs
            if pt.get("serial_lock")
        ]

        self.testing_readers = [
            TestingReader(
                port=pt["port"],
                baudrate=baudrate,
                serial_lock=cast(Lock, pt["serial_lock"]),
                num_sensors=pt["pt_count"],
                name=pt["name"],
                logger=pt["logger"],
                decode_fn=pt["decode_fn"],
                stop_sequence=pt["stop_sequence"],
                expected_payload_length=pt["expected_payload_length"],
            )
            for pt in pt_configs
            if pt.get("serial_lock")
        ]

        self.num_readings_per_pt = num_readings_per_pressure
        self.hv = hv
        self.lv = lv
        super().__init__()

    def on_mount(self):
        self.push_screen(
            calibration_screen.CalibrationScreen(
                self.calibration_readers, self.num_readings_per_pt, self.hv, self.lv
            )
        )

    def action_test_calibrations(self):
        """bring up the interface for testing calibrations"""
        if isinstance(self.screen, calibration_screen.CalibrationScreen):
            self.push_screen(
                test_calibration_screen.TestCalibrationScreen(self.testing_readers)
            )

    def action_calibrate(self):
        """bring back the interface for calibrating sensors"""
        if isinstance(self.screen, test_calibration_screen.TestCalibrationScreen):
            self.pop_screen()
