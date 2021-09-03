# gps client
# Receives the sensor data from the server, organizes it into variables and saves onto an sql database

import zmq
import sys
import threading
import time
import sqlite3

IP = '169.254.16.177' #Ethernet
filter = 'LOCATION'

### FUNCTIONS ###

def append_location(context, subscriber):
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
    id = 0

    #connect to database
    conn = sqlite3.connect('gpsinfo.db')
    cur = conn.cursor() 
    ## TEMPORARY FOR TESTING ##
    cur.execute("DROP TABLE IF EXISTS info")
    conn.commit()
    ###########################
    #create table of results
    cur.execute("""CREATE TABLE IF NOT EXISTS info(
        id INT PRIMARY KEY,
        gps_time TEXT,
        AC_LAT TEXT,
        AC_LONG TEXT,
        AC_yaw TEXT,
        ac_PITCH TEXT,
        ac_roll TEXT,
        sens_yaw TEXT,
        sens_roll TEXT,
        sens_pitch TEXT)
    """)
    conn.commit()

    #append date in loop
    while True:
        string = subscriber.recv_string()
        string = string.split(',')
        gps_time = string[1]
        AC_LAT = string[2]
        AC_LONG = string[3]
        accel_x = string[4]
        accel_y = string[5]
        accel_z = string[6]
        sens_pitch = string[7]
        sens_roll = string[8]

        #string = f'[{gps_time}] LAT: {AC_LAT} LONG: {AC_LONG}' 
        #string = f'[ACCEL] X:{accel_x} Y:{accel_y} Z:{accel_z} m/s^2'
        #write date in text file
        #file = open('data.txt', 'a')
        #file.write(f'{string} \n')
        #file.close()

        #write data to sql database
        entry = (id, gps_time, AC_LAT, AC_LONG, AC_yaw, ac_PITCH, ac_roll, sens_yaw, sens_roll, sens_pitch)
        cur.execute("INSERT INTO info VALUES(?,?,?,?,?,?,?,?,?,?);", entry)
        conn.commit()

        #print table
        #cur.execute("SELECT * FROM info;")
        #results = cur.fetchall()
        #print(results)
        id += 1
        
    
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


### MAIN ###

if __name__ == '__main__':
    try:
        #connect sockets
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        requester = context.socket(zmq.REQ)
        try:
            subscriber.connect(f'tcp://{IP}:5556')
            requester.connect(f'tcp://{IP}:5555')
        except:
            print("Can't connect sockets")
            sys.exit()
        subscriber.setsockopt_string(zmq.SUBSCRIBE, filter)
        subscriber.setsockopt_string(zmq.SUBSCRIBE, 'DATA')

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
