import cv2, os, sys, pickle
import time
import numpy as np
from configs import *
from datetime import datetime, date
import cv2, os, sys, pickle
import time
import numpy as np
from configs import *
from datetime import datetime, date
import sqlite3

# Database Setup
def init_db():
    try:
        conn = sqlite3.connect('attendance_v2.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database error: {e}")

init_db()

# Set to track who has been logged in this session
logged_attendees = set()

def log_attendance(name):
    """Logs the attendance to SQLite if not already logged this session"""
    if name in logged_attendees:
        return

    try:
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        
        conn = sqlite3.connect('attendance_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO logs (name, date, time, status) VALUES (?, ?, ?, ?)",
                       (name, today_date, current_time, "Present"))
        
        conn.commit()
        conn.close()
        
        print(f"Attendance logged to Database for: {name}")
        logged_attendees.add(name)
    except Exception as e:
        print(f"Error logging to Database: {e}")

faceCascade = cv2.CascadeClassifier('bin/haarcascade_frontalface_default.xml')
profileCascade = cv2.CascadeClassifier('bin/haarcascade_profileface.xml')

recognizer = cv2.face.LBPHFaceRecognizer_create()

if not os.path.exists('face_rec_saved_model.yaml'):
    print("Error: Model file 'face_rec_saved_model.yaml' not found!")
    print("Please run 'python Train_Images.py' first to train the model.")
    sys.exit(1)

recognizer.read('face_rec_saved_model.yaml')

with open(label_name_map_file, 'rb') as handle:
        label_name_map = pickle.load(handle)

print("Press 'q' to quit\n\n\n")

def predictFacesFromWebcam(label2name_map):
        video_capture = cv2.VideoCapture(0)
        while True:
                ret, frame = video_capture.read()
                print(ret)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(gray, scaleFactor, minNeighbors, cascadeFlags, minSize)
                for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        name_predicted, confidence = recognizer.predict(cv2.resize(gray[y: y + h, x: x + w], face_resolution))
                        print(str(name_predicted) +' , ' +str(confidence))
                        if(name_predicted!=0 and confidence<confidence_threshold):
                                name = label2name_map[name_predicted]
                                print("It is predicted as "+name)
                                cv2.putText(frame, name, (x+3,y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0))
                                log_attendance(name)
                                
                cv2.imshow('Video', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\nQuitting")
                        break
        video_capture.release()
        cvcv2.destroyAllWindows()
predictFacesFromWebcam(label_name_map)
