# Receive GPS Playback
# connects to publisher and receives data sent from gps_playback.py

import sqlite3
import time
import datetime
import zmq
import sys
import threading 
from queue import Queue 

### FUNCTION DEFINITIONS ###

#checks to see if the value entered is a number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#checks to see if the value entered is a time
def is_time(s):
    try:
        time.strptime(s, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False

#ask the user for the start date and speed of playback
def configure_playback(requester, q):
    time_speed = 1
    #stop running if time_speed is entered as zero
    while(time_speed != 0):
        #ask for start date and playback speed
        time_start = input('Please enter start time in the form of [YYYY-MM-DD HH:MM]: ')
        while(not is_time(time_start)):
            print('Invalid entry, enter a valid time')
            time_start = input('Please enter start time in the form of [YYYY-MM-DD HH:MM]: ')

        time_speed = input('Please enter the speed of delivery as a float (1.0 for normal speed, 2.0 for 2x speed, etc): ')
        while(not is_number(time_speed)):
            print('Invalid entry, enter a number')
            time_speed = input('Please enter the speed of delivery as a float (1.0 for normal speed, 2.0 for 2x speed, etc): ')

        #send the configuration to replier 
        configure = f'{time_start},{time_speed}'
        requester.send_string(configure)

        #if entered time is zero, exit
        if(int(time_speed) == 0):
            break

        #get the reply
        playback_results = requester.recv_string()
        print(playback_results)

    print('Exiting req')
    #send message to sub for exit
    q.put('exit')

def display_playback(subscriber, q):
    #print out playback
    while True:
        #if told to exit, exit
        if(q.get() == 'exit'):
            break
        string = subscriber.recv_string()
        print(string)

    print('Exiting sub')
    

### MAIN ###

if __name__ == '__main__':

    IP = '192.168.1.142' #"169.254.16.177" #Ethernet 
    #connect with zmq
    try:
        # Prepare our context and sockets
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        requester = context.socket(zmq.REQ)
        try:
            subscriber.connect(f"tcp://{IP}:5555")
            subscriber.setsockopt_string(zmq.SUBSCRIBE, 'PLAYBACK')
            requester.connect(f"tcp://{IP}:5556")
            print('Sockets connected')
        except:
            print("Can't connect sockets")

        q = Queue()
        #threading
        t1 = threading.Thread(target=display_playback, args=[subscriber, q])
        t2 = threading.Thread(target=configure_playback, args=[requester, q])
        t1.start()
        t2.start()
         

    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
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


 
 