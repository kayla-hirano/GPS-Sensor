# GPS PLAYBACK
# Reads from a .db file and sends the information 


import sqlite3
import time
import datetime
import zmq
import sys

#checks to see if the value entered is a number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

if __name__ == '__main__':

    IP = '192.168.1.142' #"169.254.16.177" #Ethernet 
    #connect with zmq
    try:
        # Prepare our context and sockets
        context = zmq.Context()
        publisher = context.socket(zmq.PUB)
        try:
            publisher.bind(f"tcp://{IP}:5555")
        except:
            print("Can't bind sockets")
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

        #ask for start date and playback speed
        #DEBUG: Add exceptions of time_start (if user enters it in the wrong format, etc)
        time_start = input('Please enter start time in the form of [HH:MM]: ')

        time_speed = input('Please enter the speed of delivery as a float (1.0 for normal speed, 2.0 for 2x speed, etc): ')
        while(not is_number(time_speed)):
            print('Invalid entry, please try again')
            time_speed = input('Please enter the speed of delivery as a float (1.0 for normal speed, 2.0 for 2x speed, etc): ')
     
        #retrieve lines from table 
        conn = sqlite3.connect('gpsinfo.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM info;")
        results = cur.fetchall()

        #calculate gps time interval using the first two lines
        dt_object1 = datetime.datetime.strptime(results[1][1], '%Y-%m-%d %H:%M:%S')
        dt_object2 = datetime.datetime.strptime(results[0][1], '%Y-%m-%d %H:%M:%S')
        gps_time_interval = dt_object1-dt_object2
        gps_interval = gps_time_interval.seconds

        #set to true once start time is detected
        start = False
        print("starting database read...\n")
        for line in results:
            #start sending packets when the specified time is found
            if(line[1].find(time_start) != -1):
                start = True

            if(start):
                #assign and send a packet 
                packet['id'] = line[0]
                packet['gps_time'] = line[1]
                packet['AC_LAT'] = line[2]
                packet['AC_LONG'] = line[3]
                packet['AC_yaw'] = line[4]
                packet['ac_PITCH'] = line[5]
                packet['ac_roll'] = line[6]
                packet['sens_pitch'] = line[7]
                packet['sens_roll'] = line[8]
                #enter data here
                zmqpacket = f"""PLAYBACK,{packet['id']},{packet['gps_time']},{packet['AC_LAT']},{packet['AC_LONG']},{packet['AC_yaw']},\
{packet['ac_PITCH']},{packet['ac_roll']},{packet['sens_pitch']},{packet['sens_roll']}"""
                publisher.send_string(zmqpacket)
                print(f'SENT {zmqpacket}')
         
                #wait for the specified time
                time.sleep(gps_interval/float(time_speed))

    except KeyboardInterrupt:
        print("Program interrupted...")
    finally:
        #close sockets
        publisher.close()
        #terminate context
        context.term()
        print('Done.')

