import os
import struct
import sys
from threading import Lock

from cli import cli
from config import config_setter
from logger.logger import Logger

HV = "High Voltage"
LV = "Low Voltage"

RAW_DATA_LV_FILENAME = "logs/raw_readings_lv.csv"
AVG_DATA_LV_FILENAME = "logs/avg_readings_lv.csv"
CAL_COEFFS_LV_FILENAME = "logs/cals_lv.csv"

RAW_DATA_HV_FILENAME = "logs/raw_readings_hv.csv"
AVG_DATA_HV_FILENAME = "logs/avg_readings_hv.csv"
CAL_COEFFS_HV_FILENAME = "logs/cals_hv.csv"

CONTROL_CHARACTERS = b"\r\n"


def main() -> None:
    # first get the config params
    config = config_setter.Config(hv=HV, lv=LV)

    answers = None

    try:
        answers = config.prompt()
    except KeyboardInterrupt:
        print("Set-up cancelled, exiting...")
        sys.exit(1)

    if not answers:
        print("No answers provided for set up. Exiting.")
        sys.exit(1)

    if not answers.get("pt_configs", None):
        print("No PTs to calibrate. Exiting.")
        sys.exit(1)

    for config in answers["pt_configs"]:
        config["serial_lock"] = Lock()
        config["logger"] = Logger(
            raw_data_filename=(
                RAW_DATA_HV_FILENAME if config["name"] == HV else RAW_DATA_LV_FILENAME
            ),
            avg_data_filename=(
                AVG_DATA_HV_FILENAME if config["name"] == HV else AVG_DATA_LV_FILENAME
            ),
            stored_calibration_filename=(
                CAL_COEFFS_HV_FILENAME
                if config["name"] == HV
                else CAL_COEFFS_LV_FILENAME
            ),
        )
        config["stop_sequence"] = CONTROL_CHARACTERS
        config["decode_fn"] = decode_fn
        config["expected_payload_length"] = 32 + 2  # 4 floats and 2 escape characters

    app = cli.AutoCalCli(
        pt_configs=answers["pt_configs"],
        num_readings_per_pressure=int(answers["num_readings_per_pt"]),
        baudrate=answers["baud_rate"],
        hv=HV,
        lv=LV,
    )
    app.run()


def decode_fn(line: bytes) -> list[float]:
    """Dont do error handling, let the callers do it, since their error handling logic is quite different"""
    # first remove the control characters
    line = line.removesuffix(CONTROL_CHARACTERS)
    return list(struct.unpack("8f", line))


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    main()
