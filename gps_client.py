import zmq
import sys
import threading
import time

IP = '169.254.16.177' #Ethernet
#IP = "192.168.1.10" 

filter = 'LOCATION'

### FUNCTIONS ###

def append_location(context):
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f'tcp://{IP}:5556')
    subscriber.setsockopt_string(zmq.SUBSCRIBE, filter)
    subscriber.setsockopt_string(zmq.SUBSCRIBE, 'ACCEL')
    subscriber.setsockopt_string(zmq.SUBSCRIBE, 'GYRO')

    #append date in loop
    while True:
        string = subscriber.recv_string()
        if 'LOCATION' in string:
            gps_values = string.split(',')
            AC_LAT = gps_values[1][11:]
            AC_LONG = gps_values[2][12:]
            gps_time = gps_values[0][9:]

        #write date in text file
        file = open('data.txt', 'a')
        file.write(f'{string} \n')
        file.close()
    
def request_photo(context):
    requester = context.socket(zmq.REQ)
    requester.connect(f'tcp://{IP}:5555')
    
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

        #  Get the reply.
        message = requester.recv_string()
        print("Data received from the server: [ %s ]" % message)

    print('STOPPED...')
    #requester.close()
    #context.term()

### CODE ###

if __name__ == '__main__':
    #define variables
    AC_LAT = ''
    AC_LONG = ''
    AC_yaw = ''
    ac_PITCH = 0
    ac_roll = 0
    sens_yaw = 0
    sens_roll = ''
    sens_pitch = ''
    gps_time = ''

    context = zmq.Context()

    #threading
    t1 = threading.Thread(target=append_location, args=[context])
    t2 = threading.Thread(target=request_photo, args=[context])

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print('Done')
