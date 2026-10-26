import ipaddress
import json
import os
import struct
import subprocess
import sys
from pathlib import Path
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
PI_SSH_USER = "ares_gs"
PI_CALIBRATION_DIR = "/home/ares_gs/synnax_node/scripts/logs"


def upload_calibrations(app: cli.AutoCalCli, pi_ip: str) -> None:
    if not pi_ip:
        return

    parsed_ip = ipaddress.ip_address(pi_ip)
    ssh_host = f"[{pi_ip}]" if parsed_ip.version == 6 else pi_ip
    group_names = {"High-Voltage": "hv", "Low-Voltage": "lv"}
    for reader in app.calibration_readers:
        coefficients = reader.calibration_coefficients
        if coefficients is None:
            continue

        group = group_names[reader.get_pt_id()]
        calibration_path = Path("logs") / f"pt_calibration_{group}.json"
        calibration = {
            "slope": [
                coefficients[index][0] if index in coefficients else None
                for index in range(reader.get_num_pts())
            ],
            "intercept": [
                coefficients[index][1] if index in coefficients else None
                for index in range(reader.get_num_pts())
            ],
            "selected_indices": reader.selected_sensor_indices,
        }
        with calibration_path.open("w", encoding="utf-8") as calibration_file:
            json.dump(calibration, calibration_file, indent=2)
            calibration_file.write("\n")

        remote_path = f"{PI_CALIBRATION_DIR}/pt_calibration_{group}.json"
        try:
            subprocess.run(
                [
                    "scp",
                    str(calibration_path),
                    f"{PI_SSH_USER}@{ssh_host}:{remote_path}",
                ],
                check=True,
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                "OpenSSH scp was not found. Install/enable the OpenSSH client "
                "or leave the Pi IP blank to skip upload."
            ) from error
        print(f"Uploaded {group.upper()} calibration to {PI_SSH_USER}@{pi_ip}.")


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

    if not answers.get("data_format", None):
        print("No data format specified. Exiting.")
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
        config["decode_fn"] = (
            new_decode_fn
            if answers["data_format"] == "New Format (with board timestamps)"
            else old_decode_fn
        )
        config["expected_payload_length"] = (
            40 + 2
            if answers["data_format"] == "New Format (with board timestamps)"
            else 32 + 2
        )

    app = cli.AutoCalCli(
        pt_configs=answers["pt_configs"],
        num_readings_per_pressure=int(answers["num_readings_per_pt"]),
        baudrate=answers["baud_rate"],
        hv=HV,
        lv=LV,
    )
    app.run()
    upload_calibrations(app, answers["pi_ip"])


def old_decode_fn(line: bytes) -> list[float]:
    """Dont do error handling, let the callers do it, since their error handling logic is quite different"""
    # first remove the control characters
    line = line.removesuffix(CONTROL_CHARACTERS)
    return list(struct.unpack("8f", line))


def new_decode_fn(line: bytes) -> list[float]:
    """New format of data with board timestamp and packet count at the end"""
    line = line.removesuffix(CONTROL_CHARACTERS)
    return list(struct.unpack("8f2I", line))[:-2]


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    main()
