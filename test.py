import serial
import time

if __name__ == '__main__':
    gps = serial.Serial('/dev/serial0', 9600)
    while True:
        location_string = gps.readline().decode()
        if location_string[:6] == '$GPRMC':
            print(location_string)
        time.sleep(1)
    