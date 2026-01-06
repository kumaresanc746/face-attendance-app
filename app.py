from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, Response
import sqlite3
import functools
import cv2
import os
import pickle
import numpy as np
from datetime import datetime
from PIL import Image
from configs import *

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me_in_production'  # Required for session

# Database Helper
def get_db_connection():
    conn = sqlite3.connect('attendance_v2.db')
    conn.row_factory = sqlite3.Row
    return conn

init_db()

# Load Face Recognition Model
faceCascade = cv2.CascadeClassifier(cascadePath)
recognizer = cv2.face.LBPHFaceRecognizer_create()

if os.path.exists(outfile):
    recognizer.read(outfile)
    with open(label_name_map_file, 'rb') as handle:
        label_name_map = pickle.load(handle)
else:
    label_name_map = {}
    print("Warning: Model file not found. Please train images first.")

# Set to track who has been logged in this session
logged_attendees = set()

def log_attendance_web(name):
    """Logs the attendance to SQLite if not already logged this session"""
    if name in logged_attendees:
        return

    try:
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        
        conn = get_db_connection()
        conn.execute("INSERT INTO logs (name, date, time, status) VALUES (?, ?, ?, ?)",
                       (name, today_date, current_time, "Present"))
        conn.commit()
        conn.close()
        
        logged_attendees.add(name)
    except Exception as e:
        print(f"Error logging to Database: {e}")

def gen_frames():
    """Video streaming generator function."""
    camera = cv2.VideoCapture(0)  # Use 0 for local webcam or URL for IP cam
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray, scaleFactor, minNeighbors, cascadeFlags, minSize)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                if label_name_map:
                    try:
                        name_predicted, confidence = recognizer.predict(cv2.resize(gray[y:y+h, x:x+w], face_resolution))
                        if name_predicted != 0 and confidence < confidence_threshold:
                            name = label_name_map.get(name_predicted, "Unknown")
                            cv2.putText(frame, name, (x + 3, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0))
                            log_attendance_web(name)
                        else:
                            cv2.putText(frame, "Unknown", (x + 3, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255))
                    except Exception as e:
                        print(f"Prediction error: {e}")

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Login Decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == '1234':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Credentials! Try admin/1234')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template('index.html')

@app.route('/students')
@login_required
def students_page():
    return render_template('students.html')

# API Endpoints
@app.route('/api/stats')
@login_required
def get_stats():
    conn = get_db_connection()
    
    # Total Students
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    
    # Present Today (Unique names)
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    present_today = conn.execute('SELECT COUNT(DISTINCT name) FROM logs WHERE date = ?', (today,)).fetchone()[0]
    
    # Class Breakdown (Renamed from Departments)
    dept_stats = conn.execute('SELECT class_name, COUNT(*) as count FROM students GROUP BY class_name').fetchall()
    dept_data = {row['class_name']: row['count'] for row in dept_stats}
    
    conn.close()
    return jsonify({
        'total_students': total_students,
        'present_today': present_today,
        'departments': dept_data
    })

@app.route('/api/recent_attendance')
@login_required
def get_recent_attendance():
    """Fetch recent logs joined with student details"""
    conn = get_db_connection()
    # Left join to get class/year even if student not in students table yet
    query = '''
        SELECT l.*, s.class_name, s.year 
        FROM logs l 
        LEFT JOIN students s ON l.name = s.name 
        ORDER BY l.timestamp DESC LIMIT 50
    '''
    logs = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(row) for row in logs])

@app.route('/api/students', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_students():
    conn = get_db_connection()
    
    if request.method == 'POST':
        data = request.json
        try:
            conn.execute('INSERT OR REPLACE INTO students (name, class_name, year, phone) VALUES (?, ?, ?, ?)',
                         (data['name'], data['class_name'], data['year'], data.get('phone', '')))
            conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)})
        finally:
            conn.close()

    if request.method == 'DELETE':
        name = request.args.get('name')
        try:
            conn.execute('DELETE FROM students WHERE name = ?', (name,))
            conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)})
        finally:
            conn.close()
            
    # GET method
    students = conn.execute('SELECT * FROM students ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(row) for row in students])

@app.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html')

@app.route('/api/clear_logs', methods=['POST'])
@login_required
def clear_logs():
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM logs')
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conn.close()

@app.route('/api/factory_reset', methods=['POST'])
@login_required
def factory_reset():
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM logs')
        conn.execute('DELETE FROM students')
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conn.close()

@app.route('/video_feed')
@login_required
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
