gps_server 
    connects to a raspberry pi with a camera, gyrometer/accelerometer, and gps attached
    Receives data from the sensors and sends to gps_client 

gps_client
    takes the data from gps_server, assigns to variables and saves to a sql database. 
    also have the option to take a picture with the camera and put the picture on a samba file server

test, test2, test3
    test files for the camera, gyrometer/accelerometer, and gps

playback_server
    reads the data from the sql database and can playback the information. 
    Can choose a start time and the speed of playback

playback_client
    prints the data from playback_server


---- OLDER ----


gps_playback
    reads the data from the sql database and can playback the information. 
    Can choose a start time and the speed of playback

receive_playback
    prints the data from gps_playback
