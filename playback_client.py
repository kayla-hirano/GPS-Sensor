# Receive GPS Playback
# connects to publisher and receives data sent from gps_playback.py

#IDEA: user can input either start time or speed, no need to enter both

import sqlite3
import time
import datetime
import zmq
import sys
import threading 

exitCode = 'PLAYBACK, exit'
IP = #Ethernet 

#################
### FUNCTIONS ###
#################

def is_number(s):
    """Checks to see if a value is a number
    Input: value s
    Returns: Boolean
    """
    try:
        float(s)
        return True
    except ValueError:
        return False

def is_time(s):
    """Checks to see if a value is in a valid time format
    Input: value s
    Returns: Boolean
    """
    try:
        time.strptime(s, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False


def configure_playback(requester):
    """Receives info from user about desired start time and playback speed,
    sends the info to REP socket, then receieves the reponse
    Input: zmq REQ socket
    Returns: Nothing
    """
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

    print('Exiting req...')

def display_playback(subscriber):
    """Receives database info from PUB socket and writes to playback.txt
    Input: zmq SUB socket
    Returns: Nothing
    """
    #print out playback
    while True:
        string = subscriber.recv_string()
        #if told to exit, exit
        if(string == exitCode):
            break
        else:
            #write playback to a txt file for now
            file = open('playback.txt', 'a')
            file.write(f'{string} \n')
            file.close()

    print('Exiting sub...')
    
############    
### MAIN ###
############

if __name__ == '__main__':
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

        #threading
        t1 = threading.Thread(target=display_playback, args=[subscriber])
        t2 = threading.Thread(target=configure_playback, args=[requester])
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


 
 
