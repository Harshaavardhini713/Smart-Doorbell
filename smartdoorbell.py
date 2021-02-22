import face_recognition
import cv2
import numpy as np
import RPi.GPIO as GPIO
import sys
import time
import smtplib
from urllib.request import urlopen
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

key = "YWDIRHZG0A20NH6P"
baseURL = "https://api.thingspeak.com/update?api_key=%s" % key

GPIO.setmode(GPIO.BOARD)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_UP)

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
GMAIL_USERNAME = 'rithwik.iot.test@gmail.com'
GMAIL_PASSWORD = '*********' #Enter password here

class Emailer:
    def sendmail(self, recipient, subject, content, image):
        emailData = MIMEMultipart()
        emailData['Subject'] = subject
        emailData['To'] = recipient
        emailData['From'] = GMAIL_USERNAME
       
        emailData.attach(MIMEText(content))
       
        imageData = MIMEImage(open(image, 'rb').read(), 'jpg')
        imageData.add_header('Content-Disposition', 'attachment; filename="visitor.jpg"')
        emailData.attach(imageData)
       
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls()
        session.ehlo()
       
        session.login(GMAIL_USERNAME, GMAIL_PASSWORD)
       
        session.sendmail(GMAIL_USERNAME, recipient, emailData.as_string())
        session.quit

def pushbutton():
    try:
        conn = urlopen(baseURL + "&field1=1")
        print(conn.read())
        conn.close()
    except:
        print("connection failed")

def mailimage():
    sender = Emailer()

    image = '/home/pi/iot-project-smart-doorbell/image.jpg'
    sendTo = 'rithwik.chithreddy2000@gmail.com'
    emailSubject = "Smart Doorbell has a Visitor"
    emailContent = "%s has visited your house" % name
    sender.sendmail(sendTo, emailSubject, emailContent, image)
    print("Email Sent")

video_capture = cv2.VideoCapture(0)

rithwik_image = face_recognition.load_image_file("/home/pi/iot-project-smart-doorbell/rithwik.jpg")
rithwik_face_encoding = face_recognition.face_encodings(rithwik_image)[0]
eishika_image = face_recognition.load_image_file("/home/pi/iot-project-smart-doorbell/eishika.jpg")
eishika_face_encoding = face_recognition.face_encodings(eishika_image)[0]

known_face_encodings = [
    rithwik_face_encoding,
    eishika_face_encoding
]
known_face_names = [
    "Rithwik",
    "Eishika"
]

face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

while True:
    ret, frame = video_capture.read()
   
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
   
    rgb_small_frame = small_frame[:, :, ::-1]
   
    if process_this_frame:
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
       
        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
           
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
           
            face_names.append(name)

    process_this_frame = not process_this_frame
   
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4
       
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
       
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
   
    cv2.imshow('Video', frame)

    input_state = GPIO.input(10)
    if input_state == 0:
        cv2.imwrite('/home/pi/iot-project-smart-doorbell/image.jpg', frame)
        pushbutton()
        print("Send data to ThingSpeak")
        mailimage()
   
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
