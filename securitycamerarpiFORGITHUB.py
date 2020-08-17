# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy as np
from smbus import SMBus
import os
import sys
import datetime
import boto3
import threading
from twilio.rest import Client

#account information for twilio
account_sid="ACc36e67673924df1fb7c404745cc3c77e"
#This is where you would put the auth_token for twilio, I removed mine for privacy which breaks the program
auth_token =""

#initializing twilio client
client = Client(account_sid, auth_token)

    
class MyDb(object):

    def __init__(self, Table_Name='Sensor_data'):
        self.Table_Name=Table_Name

        self.db = boto3.resource('dynamodb')
        self.table = self.db.Table(Table_Name)

        self.client = boto3.client('dynamodb')

    @property
    def get(self):
        response = self.table.get_item(
            Key={
                'Sensor_Id':"1"
            }
        )

        return response

    def put(self, Sensor_Id='' , Distance='', Sound=''):
        self.table.put_item(
            Item={
                'Sensor_Id':Sensor_Id,
                'Distance':Distance,
                'Sound' :Sound
            }
        )

    def delete(self,Sensor_Id=''):
        self.table.delete_item(
            Key={
                'Sensor_Id': Sensor_Id
            }
        )

    def describe_table(self):
        response = self.client.describe_table(
            TableName='Sensor'
        )
        return response

#counter counts the number of times data is sent to aws
counter=0

addr = 0x8 # bus address
bus = SMBus(1) # indicates /dev/ic2-1

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 30
camera.rotation = 180
rawCapture = PiRGBArray(camera, size = (640, 480))
avg = None #avg will store a rolling average out the frame values of the camera so that small changes eventually dissappear

#try_io() will call a function 10 times to avoid any failed attempts
def try_io(call, tries=10):
    assert tries > 0
    error = None
    result = None

    while tries:
        try:
            result = call()
        except IOError as e:
            error = e
            tries -= 1
        else:
            break

    if not tries:
        raise error

    return result


# allow the camera to adjust to lighting/white balance
time.sleep(2)

# initiate video or frame capture sequence
for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # grab the raw array representation of the image
    frame = f.array
    
    # convert imags to grayscale &  blur the result
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    # inittialize avg if it hasn't been done
    if avg is None:
        avg = gray.copy().astype("float")
        rawCapture.truncate(0)
        continue
    
    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, avg, 0.05)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    # coonvert the difference into binary & dilate the result to fill in small holes
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    

    #a stores entire register data of register 0 of arduino
    a=try_io(lambda: bus.read_i2c_block_data(addr,0))
    #distance_cm extracts distance data from registers
    distance_cm=a[0]+(a[1]*16)+(a[2]*16*16)+(a[3]*16*16*16)
    #b is the bit value of the stored sound detector values
    b=a[4]
    if b==1:
        cv2.putText(frame, "Sound detected", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        sound_detected="Sound detected"
    else:
        cv2.putText(frame, "Sound not detected", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        sound_detected="Sound not detected"
    cv2.putText(frame, str(distance_cm)+"cm", (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    obj = MyDb()
    obj.put(Sensor_Id=str(counter), Distance=str(distance_cm), Sound=str(sound_detected))
    counter = counter + 1
    print("Uploaded Sample on Cloud D:{},S:{} ".format(distance_cm, sound_detected))

    # find contours or continuous white blobs in the image
    contours, hierarchy = cv2.findContours(thresh.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    
    # find the index of the largest contour
    if len(contours) > 0:
        areas = [cv2.contourArea(c) for c in contours]
        max_index = np.argmax(areas)
        cnt=contours[max_index]   

        # draw a bounding box/rectangle around the largest contour
        x,y,w,h = cv2.boundingRect(cnt)
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
        area = cv2.contourArea(cnt)

        #if a detection is present, send text message to myself
        if area>100 and b and distance_cm<=10:
            #place personal phone number in "to" and twilio phone number in "from" below
            message = client.api.account.messages.create(to="",from_="",body="Intruder Alert!")
            
    
        # add text to the frame
        cv2.putText(frame, "Largest Contour", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    # show the frame
    cv2.imshow("Video", frame)   

    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)

    # if the 'q' key is pressed then break from the loop
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    
cv2.destroyAllWindows()
