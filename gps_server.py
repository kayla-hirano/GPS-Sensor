import time
import threading
import zmq
import datetime
import random
import sys
import serial
import board
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
from picamera import PiCamera

IP = "169.254.16.177" #Ethernet 
#IP = "192.168.1.164" 

#GPS = '$GPRMC,064951.000,A,2307.1256,N,12016.4438,E,0.03,165.48,260406,3.05,W,A*2C' #placeholder for actual info

### FUNCTIONS ###

def send_location(context):
    publisher = context.socket(zmq.PUB)
    try:
        publisher.bind(f"tcp://{IP}:5556")
    except:
        print("Can't bind publisher")
        sys.exit()

    gps = serial.Serial('/dev/serial0', 9600)
    i2c = board.I2C()  # uses board.SCL and board.SDA
    sensor = LSM6DSOX(i2c)
    
    # format and send data in a loop
    while True:
        current_date = datetime.datetime.now()
        formatted_date = current_date.strftime("%Y-%m-%d %H:%M:%S")

        location_string = gps.readline().decode()
        if location_string[:6] == '$GPRMC':
            location_array = location_string.split(',')
            latitude = location_array[3][:-7] + ' ' + location_array[3][-7:] + ' ' + location_array[4]
            longitude = location_array[5][:-7] + ' ' + location_array[5][-7:] + ' ' + location_array[6]

            #send location to client
            location = f'{formatted_date}, Latitude: {latitude}, Longitude: {longitude}'
            publisher.send_string(f"LOCATION {location}")
            location_to_send = location
            print("Sent [%s] " % location_to_send)
            
            #send acceleration and gyro to client
            #TODO: calculate pitch, yaw, and roll
            accel = "Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (sensor.acceleration)
            publisher.send_string(f"ACCEL {accel}")
            print("Sent [%s] " % accel)
            gyro = "Gyro X:%.2f, Y: %.2f, Z: %.2f radians/s" % (sensor.gyro)
            publisher.send_string(f"GYRO {gyro}")
            print("Sent [%s] " % gyro)

            #  wait for 5 seconds
            time.sleep(5)

def rand_reply(context):
    replier = context.socket(zmq.REP)
    try:
        replier.bind(f"tcp://{IP}:5555")
    except:
        print("Can't bind replier")
        sys.exit()
    
    camera = PiCamera()
    while True:
        #  Wait for next request from client
        message = replier.recv_string()
        print("Received request: %s" % message)
        #  Do some 'work'
        time.sleep(1)

        if message == 'SNAP':
            camera.start_preview()
            sleep(5)
            #take picture
            camera.capture('/share/test_image%s.jpg' %i)
            camera.stop_preview()
            i = i + 1
            to_client = 'picture'
        elif message == 'STOP':
            replier.send_string('STOP')
            to_client = 'STOP'
        else:
            replier.send_string('INVALID')
            to_client = 'INVALID, PLEASE ENTER A VALID COMMAND'

        print('Sent %s to client' % to_client)


### CODE ###

if __name__ == '__main__':
    # Prepare our context and sockets
    context = zmq.Context()
    i = 1

    #threading
    t1 = threading.Thread(target=send_location, args=[context])
    t2 = threading.Thread(target=rand_reply, args=[context])

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print('Done')
