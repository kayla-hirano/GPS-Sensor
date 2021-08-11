from picamera import PiCamera
from time import sleep

i = 1
camera = PiCamera()
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
        
    if command == 'SNAP':
        #show preview for 5 seconds (only works on seperate monitor)
        camera.start_preview()
        sleep(5)
        #take picture
        #camera.capture('/home/pi/Desktop/pacom-rif-gps/image.jpg')
        camera.capture('/share/test_image%s.jpg' %i)
        camera.stop_preview()
        print('image saved as test_image%s.jpg' %i)
        i = i+1
            

print('STOPPED...')