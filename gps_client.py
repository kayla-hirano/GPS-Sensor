import zmq
import sys
import threading
import time

#IP = '169.254.210.83' #Ethernet 
IP = "192.168.1.136" 

filter = 'LOCATION'

### FUNCTIONS ###

def append_location(context):
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f'tcp://{IP}:556')
    subscriber.setsockopt_string(zmq.SUBSCRIBE, filter)

    #append date in loop
    while True:
        string = subscriber.recv_string()
        #write date in text file
        file = open('gps.txt', 'a')
        file.write(f'{string[9:]} \n')
        file.close()
    
def request_rand(context):
    requester = context.socket(zmq.REQ)
    requester.connect(f'tcp://{IP}:555')
    
    #print command list
    command = ''
    time.sleep(1)
    print("""
        Please select from the following commands:\n
        --------------------------------------------------\n
        --- RANDOM for random number between 1 and 100 ---\n
        --- STOP to disconnect ---------------------------\n
        --------------------------------------------------""")
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

### CODE ###

if __name__ == '__main__':
    context = zmq.Context()

    #threading
    t1 = threading.Thread(target=append_location, args=[context])
    t2 = threading.Thread(target=request_rand, args=[context])

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print('Done')
