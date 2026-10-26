import ipaddress
from typing import cast

import inquirer
import serial
from inquirer import errors as inquirer_errors

from auto_cal_types import ConfigFields


def validate_number(answers, current) -> bool:
    try:
        int(current)
        return True
    except ValueError:
        raise inquirer_errors.ValidationError("", reason="Invalid number")


def parse_sensor_indices(current: str) -> list[int]:
    try:
        indices = [int(value.strip()) for value in current.split(",")]
    except ValueError as error:
        raise ValueError("Enter PT channel indices separated by commas") from error

    if not indices or any(index < 0 or index >= 8 for index in indices):
        raise ValueError("PT channel indices must be between 0 and 7")
    if len(indices) != len(set(indices)):
        raise ValueError("PT channel indices must not be repeated")
    return indices


def validate_sensor_indices(answers, current) -> bool:
    try:
        parse_sensor_indices(current)
        return True
    except ValueError as error:
        raise inquirer_errors.ValidationError("", reason=str(error)) from error


def validate_port(answers, current) -> bool:
    """Check that the selected port is open"""
    try:
        ser = serial.Serial(current, int(answers["baud_rate"]), timeout=1)
        ser.close()
        return True
    except serial.SerialException:
        raise inquirer_errors.ValidationError(
            "", reason=f"{current} is currently in use"
        )


def validate_ip(answers, current) -> bool:
    """Validate an optional Raspberry Pi IPv4 or IPv6 address."""
    if not current:
        return True
    try:
        ipaddress.ip_address(current)
        return True
    except ValueError:
        raise inquirer_errors.ValidationError("", reason="Invalid IP address")


PORT_HV = (
    "/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_B4:3A:45:B3:70:B0-if00"
)
PORT_LV = (
    "/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_B4:3A:45:B6:7E:D0-if00"
)


class Config:
    def __init__(self, hv: str, lv: str):
        self.HV = "High Voltage"
        self.LV = "Low Voltage"

        # split the questions into multiple stages so that we can ask questions conditionally
        self.question_stage_one = [
            inquirer.Text(
                "baud_rate",
                message="Controller baud rate",
                validate=validate_number,
            ),
            inquirer.Checkbox(
                "ports_to_read",
                message="Select the PT groups you wish to calibrate (space to select, ENTER to confirm)",
                choices=[self.HV, self.LV],
            ),
            inquirer.List(
                "data_format",
                message="Select the data format",
                choices=[
                    "New Format (with board timestamps)",
                    "Old format (without board timestamps)",
                ],
            ),
            inquirer.Text(
                "pi_ip",
                message="Raspberry Pi IP for SSH/SCP (leave blank to skip upload)",
                validate=validate_ip,
                default="",
            ),
        ]

    def prompt(self) -> ConfigFields | None:
        answers = inquirer.prompt(
            self.question_stage_one, raise_keyboard_interrupt=True
        )

        if (
            not answers
            or not (groups_to_read := answers.get("ports_to_read"))
            or not answers.get("data_format")
        ):
            return answers

        del answers["ports_to_read"]
        pt_configs = []
        if self.HV in groups_to_read:
            hv_selection = inquirer.prompt(
                [
                    inquirer.Text(
                        "hv_indices",
                        message="HV PT indices to calibrate (0-7, comma-separated)",
                        validate=validate_sensor_indices,
                    )
                ],
                raise_keyboard_interrupt=True,
            )
            if hv_selection:
                pt_configs.append(
                    {
                        "port": PORT_HV,
                        "pt_count": 8,
                        "selected_sensor_indices": parse_sensor_indices(
                            hv_selection["hv_indices"]
                        ),
                        "name": self.HV,
                    }
                )

        if self.LV in groups_to_read:
            lv_selection = inquirer.prompt(
                [
                    inquirer.Text(
                        "lv_indices",
                        message="LV PT indices to calibrate (0-7, comma-separated)",
                        validate=validate_sensor_indices,
                    )
                ],
                raise_keyboard_interrupt=True,
            )
            if lv_selection:
                pt_configs.append(
                    {
                        "port": PORT_LV,
                        "pt_count": 8,
                        "selected_sensor_indices": parse_sensor_indices(
                            lv_selection["lv_indices"]
                        ),
                        "name": self.LV,
                    }
                )

        answers["pt_configs"] = pt_configs

        # ask the remaining question
        num_readings_per_pt = inquirer.prompt(
            [
                inquirer.Text(
                    "num_readings_per_pt",
                    message="Number of readings to take per pt",
                    validate=validate_number,
                    default=10,
                ),
            ],
            raise_keyboard_interrupt=True,
        )

        if num_readings_per_pt:
            answers.update(num_readings_per_pt)

        return cast(ConfigFields, answers)
