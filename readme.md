**Automated Calibration for PTs and LCs**

<hr />

[https://github.com/user-attachments/assets/e053b715-f8eb-429d-b119-fccfdb684d5d](https://github.com/user-attachments/assets/33f6f05b-e23b-4285-9055-7b601c444aa7)

<hr />

![Auto Cal Flow](./assets/auto-cal-flow.png "Program Flow")

<hr />

**Set-up instructions**

1. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:

   On Windows:

   ```bash
   venv\Scripts\activate
   ```

   On macOS/Linux:

   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run project
   ```bash
   python src/main.py
   ```

5. See the secondary usage note below for selecting channels and optionally
   transferring calibration coefficients to the Raspberry Pi.

<hr />

**To-do**

<ul>
  <li>
  Disable input box: while taking readings & after the calibrations are complete </li>
  <li>Improve error messaging </li>
  <li>Separate average value calculation and reading from serial</li>
</ul>

<hr />

**Secondary usage note: sending PT calibrations to the Raspberry Pi**

Auto-Cal can calibrate selected channels and optionally transfer their
coefficients to the Pi for use by the combined `pt_2.py` node.

1. Start Auto-Cal and enter the baud rate.
2. Select the HV and/or LV group(s), then enter the selected PT indices for
   each group separately as comma-separated values from `0` through `7`. For
   example, if calibrating HV PTs 0, 1, and 6 and LV PTs 1 and 4, enter `0,1,6`
   for HV and `1,4` for LV. Indices are zero-based within each group; LV index
   `0` maps to `pt8`, and LV index `1` maps to `pt9`.
3. Select the controller data format, optionally enter the Raspberry Pi's IP
   address, and choose the number of readings per pressure.
4. Apply known pressures and enter each value in Auto-Cal. Collect at least two
   distinct pressure points for each selected PT.
5. Press `Ctrl+G` to calculate the regression coefficients. Review the results.
6. When finished, exit Auto-Cal. If an IP address was provided, Auto-Cal writes
   and transfers the selected HV and/or LV coefficient files with `scp`. Leave
   the IP blank to skip transfer.

For transfer, the computer needs the OpenSSH client, and its SSH public key
must be authorized for the `ares_gs` account on the Pi. The private key remains
on the computer. Auto-Cal copies the files to
`/home/ares_gs/synnax_node/scripts/logs/`.

The Pi's `pt_2.py` node reads the JSON files at startup and checks for updates
while running. It applies coefficients to the selected channels. Unselected
channels remain unscaled. The Pi does not need serial interaction to receive
these files. Its existing serial connections remain in use for reading live
sensor data. This transfer workflow applies to `pt_2.py`, not the separate
`pt_hv.py`, `pt_lv.py`, load-cell, or thermocouple scripts.

In `pt_2.py`, `USE_AUTOCAL_JSON` selects the calibration source. Set it to
`True` to use Auto-Cal's JSON files, or `False` to use the `MANUAL_SLOPES` and
`MANUAL_INTERCEPTS` lists in that script. Manual lists contain 16 values in
channel order (`pt0` through `pt15`); update both lists before starting the
node. Manual mode does not reload JSON file changes.
