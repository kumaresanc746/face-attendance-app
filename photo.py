import cv2, os, sys, time
import numpy as np
from PIL import Image
from configs import *
import sqlite3

# Database Helper to save student details
def save_student_details(name, class_name, year, phone):
    try:
        conn = sqlite3.connect('attendance_v2.db')
        cursor = conn.cursor()
        # Create table if it doesn't exist (just in case)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                class_name TEXT NOT NULL,
                year TEXT NOT NULL,
                phone TEXT
            )
        ''')
        
        # Insert or Update
        cursor.execute('INSERT OR REPLACE INTO students (name, class_name, year, phone) VALUES (?, ?, ?, ?)',
                       (name, class_name, year, phone))
        conn.commit()
        conn.close()
        print(f"Student {name} registered successfully in Database!")
    except Exception as e:
        print(f"Database Error: {e}")

faceCascade = cv2.CascadeClassifier('bin/haarcascade_frontalface_default.xml')
i=0

video_capture = cv2.VideoCapture(0) #Set the source webcam
video_capture .set(3,640)
video_capture .set(4,480)
print("Enter 'c' to capture the photo\n")
print("Enter 'q' to quit..\n\n")
print("Waiting to capture photo......\n\n")

while True:
        n = input("Enter: ")
        if(n=='q'):
                print("Quitting..")
                break
        if(n=='c'):
                name = input("Enter Name: ")
                class_name = input("Enter Class (e.g. B.Sc, BCA): ")
                year = input("Enter Year (e.g. 1, 2, 3): ")
                phone = input("Enter Phone Number: ")
                
                # Save details to DB
                save_student_details(name, class_name, year, phone)
                
                neram = str(int(time.time()))
                print("Capturing 30 photos automatically. Look at the camera.")
                while i<30:
                        ret, frame = video_capture.read()
                        if not ret: continue
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        faces = faceCascade.detectMultiScale(gray, scaleFactor, minNeighbors, cascadeFlags, minSize)
                        
                        # Draw rectangle around face to show it's detected
                        for (x, y, w, h) in faces:
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        cv2.imshow('Video', frame)
                        
                        # Auto-capture every ~300ms if a face is detected (optional protection) or just force capture
                        # For simplicity, we just capture. 
                        # Ideally we only save if a face is detected? 
                        # The original code just saved the frame. Let's stick to saving the frame but automatically.
                        
                        if cv2.waitKey(200) & 0xFF == ord('q'):
                            break
                            
                        cv2.imwrite(db_path+"/"+str(name)+"."+neram+str(i)+".png", gray)
                        print(f"Captured image {i+1}/30")
                        i+=1
                        
                print("Capture complete! Processing photos...")
                print("Waiting to capture photo......")

print("\n\nPROCESS STOPPED......")
video_capture.release()
