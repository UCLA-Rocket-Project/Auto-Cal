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

<hr />

**To-do**

<ul>
  <li>
  Disable input box: while taking readings & after the calibrations are complete </li>
  <li>Improve error messaging </li>
  <li>Separate average value calculation and reading from serial</li>
</ul>
