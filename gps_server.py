import time
import threading
import zmq
import sys
import math
import datetime
import serial
import board
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
from picamera import PiCamera

IP = #Ethernet 


#GPS = '$GPRMC,064951.000,A,2307.1256,N,12016.4438,E,0.03,165.48,260406,3.05,W,A*2C' #placeholder for actual info

### FUNCTIONS ###

def send_location(context, publisher, gps):
    i2c = board.I2C()  # uses board.SCL and board.SDA
    sensor = LSM6DSOX(i2c)
    
    #create data packet
    packet = {
        'date': '',
        'latitude': '',
        'longitude': '',
        'accelx': '',
        'accely': '',
        'accelz': '',
        'gyro': '',
        'senspitch': '',
        'sensroll': ''
    }
    
    # format and send data in a loop
    while True:
        current_date = datetime.datetime.now()
        gps_results = detect_location(gps).split(',')
        packet['date'] = current_date#f'{int(current_date[:2])}:{current_date[2:4]}.{current_date[4:6]}'
        packet['latitude'] = gps_results[1]
        packet['longitude'] = gps_results[2]
            
        #send acceleration and gyro to client
        packet['accelx'] = str(sensor.acceleration[0])[:6]
        packet['accely'] = str(sensor.acceleration[1])[:6]
        packet['accelz']  = str(sensor.acceleration[2])[:6]
        packet['gyro'] = "Gyro X:%.2f, Y: %.2f, Z: %.2f radians/s" % (sensor.gyro)
        
        #calculate pitch and roll
        accel_x = sensor.acceleration[0]
        accel_y = sensor.acceleration[1]
        accel_z = sensor.acceleration[2]
        packet['senspitch'] = str(-(math.atan2(accel_x, math.sqrt(accel_y*accel_y + accel_z*accel_z))*180.0)/math.pi)[:6]
        packet['sensroll'] = str((math.atan2(accel_y, accel_z)*180.0)/math.pi)[:6]
        
        #send packet
        zmqpacket = f"DATA,{packet['date']},{packet['latitude']},{packet['longitude']},{packet['accelx']},{packet['accely']},{packet['accelz']},{packet['senspitch']},{packet['sensroll']}"
        publisher.send_string(zmqpacket)
        print('SENT:')
        print(zmqpacket)
    
        #  wait for 5 seconds
        time.sleep(5)

def rand_reply(context, replier, gps): 
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
            gps_results = detect_location(gps).split(',')
            latitude = gps_results[1]
            longitude = gps_results[2]
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

def detect_location(gps):
    #get current location
    while True:
        location_string = gps.readline().decode()
        if location_string[:6] == '$GPRMC':
            location_array = location_string.split(',')
            gps_time = location_array[1]
            latitude = location_array[3][:-7] + ' ' + location_array[3][-7:] + ' ' + location_array[4]
            longitude = location_array[5][:-7] + ' ' + location_array[5][-7:] + ' ' + location_array[6]
            return f'{gps_time},{latitude},{longitude}'

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
    
        gps = serial.Serial('/dev/serial0', 9600)
        #threading
        t1 = threading.Thread(target=send_location, args=[context, publisher, gps])
        t2 = threading.Thread(target=rand_reply, args=[context, replier, gps])
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
