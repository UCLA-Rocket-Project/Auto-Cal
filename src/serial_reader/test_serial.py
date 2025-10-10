import serial
import struct

ser = serial.Serial(
    port="/dev/cu.usbserial-0001",
    baudrate=115200,
    timeout=2,
)
cnt = 0
print(ser.in_waiting, " bytes waiting to be read")

while True:
    try:
        line_hv = ser.read_until(b"\r\n", None)  # .rstrip(b'\r\n')

        print(line_hv)
        print(len(line_hv))
        # Combine data from both ESP32s (HV first, then LV),
        line = line_hv.rstrip(b"\r\n")  # HV first, then LV
        print(line)
        print(len(line))

        # Unpack the raw bytes as floats
        data = struct.unpack("8f", line)
        print(",".join([f"{val:.2f}" for val in data]))
    except KeyboardInterrupt:
        ser.close()
        break
    except:
        pass
