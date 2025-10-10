import inquirer, serial
from inquirer import errors as inquirer_errors
from serial.tools import list_ports


def validate_number(answers, current) -> bool:
    try:
        int(current)
        return True
    except ValueError:
        raise inquirer_errors.ValidationError("", reason="Invalid number")


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


PORT_HV = (
    "/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_B4:3A:45:B3:70:B0-if00"
)
PORT_LV = (
    "/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_B4:3A:45:B6:7E:D0-if00"
)


# PORT_HV = "/dev/tty.usbserial-2110"
# PORT_LV = "/dev/tty.usbserial-0001"


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
                default=115200,
            ),
            inquirer.Checkbox(
                "ports_to_read",
                message="Select the sets of PTs you wish to calibrate. (Click space to select, ENTER to confirm)",
                choices=[self.HV, self.LV],
            ),
        ]

    def prompt(self):
        answers = inquirer.prompt(
            self.question_stage_one, raise_keyboard_interrupt=True
        )

        if not answers or not (pts_to_read := answers.get("ports_to_read", None)):
            return answers

        # clean up the answers dict
        del answers["ports_to_read"]

        pt_configs = []
        if self.HV in pts_to_read:
            hv_pt_count = inquirer.prompt(
                [
                    inquirer.Text(
                        "hv_pts",
                        message="Number of PTs on HV",
                        validate=validate_number,
                    )
                ],
                raise_keyboard_interrupt=True,
            )
            if hv_pt_count:
                pt_configs.append(
                    {
                        "port": PORT_HV,
                        "pt_count": int(hv_pt_count["hv_pts"]),
                        "name": self.HV,
                    }
                )

        if self.LV in pts_to_read:
            lv_pt_count = inquirer.prompt(
                [
                    inquirer.Text(
                        "lv_pts",
                        message="Number of PTs on LV",
                        validate=validate_number,
                    )
                ],
                raise_keyboard_interrupt=True,
            )
            if lv_pt_count:
                pt_configs.append(
                    {
                        "port": PORT_LV,
                        "pt_count": int(lv_pt_count["lv_pts"]),
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

        return answers
