# Receive GPS Playback
# connects to publisher and receives data sent from gps_playback.py

import zmq
import sys 

if __name__ == '__main__':

    IP = '192.168.1.142' #"169.254.16.177" #Ethernet 
    #connect with zmq
    try:
        # Prepare our context and sockets
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        try:
            subscriber.connect(f"tcp://{IP}:5555")
            subscriber.setsockopt_string(zmq.SUBSCRIBE, 'PLAYBACK')
        except:
            print("Can't connect sockets")
            
        #print out playback
        print("Receiving playback")
        while True:
            string = subscriber.recv_string()
            print(string)

    except (Exception):
        print('Program Stopped...')
    finally:
        subscriber.close()
        #terminate context
        context.term()
        print('Done')
