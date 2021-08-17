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
#IP = "192.168.1.11" 

#GPS = '$GPRMC,064951.000,A,2307.1256,N,12016.4438,E,0.03,165.48,260406,3.05,W,A*2C' #placeholder for actual info

### FUNCTIONS ###

def send_location(context, publisher):
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
            location = f'{formatted_date},{latitude},{longitude}'
            publisher.send_string(f"LOCATION {location}")
            print("Sent [%s] " % location)
            
            #send acceleration and gyro to client
            accel_x = sensor.acceleration[0]
            accel_y = sensor.acceleration[1]
            accel_z = sensor.acceleration[2]
            accel = f'{accel_x},{accel_y},{accel_z}'
            publisher.send_string(f'ACCEL {accel}')
            print("Sent [%s] m/s^2" % accel)
            gyro = "Gyro X:%.2f, Y: %.2f, Z: %.2f radians/s" % (sensor.gyro)
            publisher.send_string(f"GYRO {sensor.gyro}")
            print("Sent [%s] " % gyro)

            #  wait for 5 seconds
            time.sleep(5)

def rand_reply(context, replier): 
    camera = PiCamera()
    i = 1
    while True:
        #  Wait for next request from client
        message = replier.recv_string()
        print("Received request: %s" % message)

        if message == 'SNAP':
            camera.start_preview()
            time.sleep(3)
            #take picture
            image_name = f'gps_image{i}.jpg'
            camera.capture(f'/share/{image_name}')
            camera.stop_preview()
            i = i + 1

            #get current location
            location_string = gps.readline().decode()
            if location_string[:6] == '$GPRMC':
                location_array = location_string.split(',')
                latitude = location_array[3][:-7] + ' ' + location_array[3][-7:] + ' ' + location_array[4]
                longitude = location_array[5][:-7] + ' ' + location_array[5][-7:] + ' ' + location_array[6]

            #format results
            image_details = f'AMAP_LOAD_IMG_OL:[{image_name}]:[DISPLAYWINDOW]:[{latitude}]:[{longitude}]:[LAT2]:[LONG2]:'
            replier.send_string(image_details)
            print(f'Sent {image_details}')
        elif message == 'STOP':
            replier.send_string('STOP request received')
            print('Sent STOP to client')
        else:
            replier.send_string('INVALID')
            print('Sent INVALID to client')



### CODE ###

if __name__ == '__main__':
    try:
        # Prepare our context and sockets
        context = zmq.Context()
        publisher = context.socket(zmq.PUB)
        replier = context.socket(zmq.REP)
        try:
            publisher.bind(f"tcp://{IP}:5556")
            replier.bind(f"tcp://{IP}:5555")
        except:
            print("Can't bind sockets")
            sys.exit()
    
        #threading
        t1 = threading.Thread(target=send_location, args=[context, publisher])
        t2 = threading.Thread(target=rand_reply, args=[context, replier])
        t1.start()
        t2.start()

    except KeyboardInterrupt:
        print("Program interrupted...")

    finally:
        #end threading
        t1.join()
        t2.join()
        #close sockets
        publisher.close()
        replier.close()
        #terminate context
        context.term()
        print('Done.')
