import serial

ser = serial.Serial(port="/dev/tty.usbserial-2110", baudrate=115200, timeout=2)
cnt = 0
print(ser.in_waiting, " bytes waiting to be read")

while True:
    try:
        ser.reset_input_buffer()
        line = ser.read_until(b"\n").decode().strip()
        print("received: ", line, cnt)
        cnt += 1
    except KeyboardInterrupt:
        ser.close()
        break
