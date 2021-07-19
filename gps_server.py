import time
import threading
import zmq
import datetime
import random

#IP = "169.254.210.83" #Ethernet 
IP = "192.168.1.136" 

GPS = '$GPRMC,064951.000,A,2307.1256,N,12016.4438,E,0.03,165.48,260406,3.05,W,A*2C' #placeholder for actual info

### FUNCTIONS ###

def send_location(context):
    publisher = context.socket(zmq.PUB)
    publisher.bind(f"tcp://{IP}:556")

    #gps = serial.Serial('/dev/serial0', 9600)
    # format and send data in a loop
    while True:
        current_date = datetime.datetime.now()
        formatted_date = current_date.strftime("%Y-%m-%d %H:%M:%S")

        # Use placeholder for now
        location_string = GPS
        #gps_info = gps.readline().decode()
        if location_string[:6] == '$GPRMC':
            location_array = location_string.split(',')
            latitude = location_array[3] + location_array[4]
            longitude = location_array[5] + location_array[6]

            location = f'[{formatted_date}] Latitude: {latitude}  Longitude: {longitude}'
            publisher.send_string(f"LOCATION {location}")
            location_to_send = location
            print("Sent [%s] " % location_to_send)

        #  wait for 5 seconds
        time.sleep(5)

def rand_reply(context):
    replier = context.socket(zmq.REP)
    replier.bind(f"tcp://{IP}:555")

    while True:
        #  Wait for next request from client
        message = replier.recv_string()
        print("Received request: %s" % message)
        #  Do some 'work'
        time.sleep(1)

        if message == 'RANDOM':
            rand_num = random.randint(1, 100)
            replier.send_string(str(rand_num))
            to_client = rand_num
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

    #threading
    t1 = threading.Thread(target=send_location, args=[context])
    t2 = threading.Thread(target=rand_reply, args=[context])

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print('Done')
