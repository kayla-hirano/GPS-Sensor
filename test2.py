import time
import board
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX

i2c = board.I2C()  # uses board.SCL and board.SDA
sensor = LSM6DSOX(i2c)

while True:
    
    accel = "Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (sensor.acceleration)
    print(accel)
    print("Gyro X:%.2f, Y: %.2f, Z: %.2f radians/s" % (sensor.gyro))
    print("")
    time.sleep(0.5)