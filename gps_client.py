import zmq
import sys
import threading
import time
import math

IP = '169.254.16.177' #Ethernet
#IP = "192.168.1.10" 

filter = 'LOCATION'

### FUNCTIONS ###

def append_location(context, subscriber):
    #append date in loop
    while True:
        string = subscriber.recv_string()
        if 'LOCATION' in string:
            gps_values = string.split(',')
            AC_LAT = gps_values[1]
            AC_LONG = gps_values[2]
            gps_time = gps_values[0][9:]
            string = f'[{gps_time}] LAT: {AC_LAT} LONG: {AC_LONG}'
        if 'ACCEL' in string:
            sensor_data = string.split(',')
            accel_x = float(sensor_data[0][6:])
            accel_y = float(sensor_data[1])
            accel_z = float(sensor_data[2])
            sens_pitch = -(math.atan2(accel_x, math.sqrt(accel_y*accel_y + accel_z*accel_z))*180.0)/math.pi
            sens_roll = (math.atan2(accel_y, accel_z)*180.0)/math.pi
            string = f'[ACCEL] X:{accel_x} Y:{accel_y} Z:{accel_z} m/s^2'

        #write date in text file
        file = open('data.txt', 'a')
        file.write(f'{string} \n')
        file.close()
    
def request_photo(context, requester):
    #print command list
    command = ''
    print("""
        Please select from the following commands:\n
        ------------------------------------------\n
        --- SNAP to take a picture ---------------\n
        --- STOP to disconnect -------------------\n
        ------------------------------------------""")
    # Keep running until STOP command
    while command != 'STOP':
        #receive command from user
        command = input('Enter command here: ')
        print("Sending request for %s" %command)
        requester.send_string(command)

        #Get the reply.
        message = requester.recv_string()
        print(message)
    raise Exception('Requested program to stop')


### CODE ###

if __name__ == '__main__':
    try:
        context = zmq.Context()
        #connect sockets
        subscriber = context.socket(zmq.SUB)
        requester = context.socket(zmq.REQ)
        try:
            subscriber.connect(f'tcp://{IP}:5556')
            requester.connect(f'tcp://{IP}:5555')
        except:
            print("Can't connect sockets")
            sys.exit()
        subscriber.setsockopt_string(zmq.SUBSCRIBE, filter)
        subscriber.setsockopt_string(zmq.SUBSCRIBE, 'ACCEL')
        subscriber.setsockopt_string(zmq.SUBSCRIBE, 'GYRO')
     

        #define variables
        AC_LAT = ''
        AC_LONG = ''
        AC_yaw = 0
        ac_PITCH = 0
        ac_roll = 0
        sens_yaw = 0
        sens_roll = ''
        sens_pitch = ''
        gps_time = ''

        #threading
        t1 = threading.Thread(target=append_location, args=[context, subscriber])
        t2 = threading.Thread(target=request_photo, args=[context, requester])

        t1.start()
        t2.start()

    except (Exception):
        print('Program Stopped...')
    finally:
        #close threads
        t1.join()
        t2.join()
        #close sockets
        requester.close()
        subscriber.close()
        #terminate context
        context.term()
        print('Done')
