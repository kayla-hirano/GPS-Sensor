# GPS PLAYBACK
# Reads from a .db file and sends the information 

import sqlite3
import time
import datetime
import zmq
import sys
import threading 
from queue import Queue 

IP = '192.168.1.142' #"169.254.16.177" #Ethernet 
exitCode = 'PLAYBACK, exit'

#################
### FUNCTIONS ###
#################

def getTimeDifference(date1, date2):
    """Receives two dates and finds the time difference
    Input: strings
    Returns: int
    """
    date1 = datetime.datetime.strptime(date1, '%Y-%m-%d %H:%M:%S')
    date2 = datetime.datetime.strptime(date2, '%Y-%m-%d %H:%M:%S')
    if date1 > date2:
      temp = date1
      date1 = date2
      date2 = temp
    return abs((date2 - date1).seconds)


def get_config(replier, q):
    """Receives info from REQ socket about desired start time and speed, 
    sends info to PUB socket, then sends reponse back to REQ socket
    Input: zmq REP socket
    Returns: Nothing
    """
    while True:
        #receive configuration from user
        configuration = replier.recv_string()
        #send config info to publisher thread
        q.put(configuration)
        #send info to user
        message = f'Config received...'
        replier.send_string(message)  
        
        config_list = configuration.split(',')
        time_speed = config_list[1]
        if(int(time_speed) == 0):
            break
    print('Exiting rep...')


def send_playback(publisher, results, q):
    """Receives info from REP socket about data playback, then
    sends packets of data from the sql database to SUB socket
    Input: zmq PUB socket
    Returns: Nothing
    """
    reg_results = results
    dt_object1 = datetime.datetime.strptime(results[0][1], '%Y-%m-%d %H:%M:%S')
    dt_object2 = datetime.datetime.strptime(results[1][1], '%Y-%m-%d %H:%M:%S')
    gps_time_interval = dt_object2-dt_object1
    gps_interval = gps_time_interval.seconds
    #define packet
    packet = {
        'id': '',
        'gps_time': '',
        'AC_LAT': '',
        'AC_LONG': '',
        'AC_yaw': 0,
        'ac_PITCH': 0,
        'ac_roll': 0, 
        'sens_pitch': '',
        'sens_roll': ''
        }

    while True:
        #when there is info from the REP thread
        if(not q.empty()):
            start = False
            results = reg_results
            print('Receieved config...')
            configuration = q.get()
            config_list = configuration.split(',')
            #seperate the start time and speed
            time_start = config_list[0]
            time_speed = config_list[1]
            time_speed = int(time_speed)
            #if the speed is negative, reverse the list
            if(time_speed < 0):
                    results = list(reversed(results))
                    time_speed = abs(time_speed)
            #if the time is zero, exit
            elif(time_speed == 0):
                print('Exiting playback...')
                break
                    
            print("Starting database read...\n")
            i = 0
            for i in range(len(results)):
                #break the loop if new config is sent
                if(not q.empty()):
                    print('Editing playback read...')
                    break
                #start sending packets when the specified time is found
                if(time_start in results[i][1]):
                    start = True
                if(start):
                    #assign and send a packet 
                    packet['id'] = results[i][0]
                    packet['gps_time'] = results[i][1]
                    packet['AC_LAT'] = results[i][2]
                    packet['AC_LONG'] = results[i][3]
                    packet['AC_yaw'] = results[i][4]
                    packet['ac_PITCH'] = results[i][5]
                    packet['ac_roll'] = results[i][6]
                    packet['sens_pitch'] = results[i][7]
                    packet['sens_roll'] = results[i][8]
                    #enter data here
                    zmqpacket = f"""PLAYBACK,{packet['id']},{packet['gps_time']},{packet['AC_LAT']},{packet['AC_LONG']},{packet['AC_yaw']},\
    {packet['ac_PITCH']},{packet['ac_roll']},{packet['sens_pitch']},{packet['sens_roll']}"""
                    #put string in queue to send to user with PUB
                    publisher.send_string(zmqpacket) 
                    print(f'SENT {zmqpacket}')

                    #calsulate time difference
                    date1 = results[i][1]
                    if (len(results)-1) == i:
                      date2 = results[i-1][1] 
                    else:
                      date2 = results[i+1][1]
                    gps_interval = getTimeDifference(date1, date2)
                    #wait for the specified time
                    time.sleep(gps_interval/float(time_speed))
                i += 1
            if(not start):
                print(f'Start time {time_start} not found') 
                publisher.send_string(f'PLAYBACK, Start time {time_start} was not found.') 

    print('Exiting pub...')
    publisher.send_string(exitCode) 
            
############    
### MAIN ###
############

if __name__ == '__main__':
    #connect with zmq
    try:
        # Prepare our context and sockets
        context = zmq.Context()
        publisher = context.socket(zmq.PUB)
        replier = context.socket(zmq.REP)
        try:
            publisher.bind(f'tcp://{IP}:5555')
            replier.bind(f'tcp://{IP}:5556')
            print('Sockets binded')
        except:
            print("Can't bind sockets")
       
        #retrieve lines from table in the sql database 
        conn = sqlite3.connect('gpsinfo.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM info;")
        results = cur.fetchall() 
        
        #define queue
        q = Queue()
        #threading
        t1 = threading.Thread(target=send_playback, args=[publisher, results, q])
        t2 = threading.Thread(target=get_config, args=[replier, q])
        t1.start()
        t2.start()

    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
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

