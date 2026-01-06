from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import sqlite3
import functools

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me_in_production'  # Required for session

# Database Helper
def get_db_connection():
    conn = sqlite3.connect('attendance_v2.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Create logs table (if not exists)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create students table (New)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            class_name TEXT NOT NULL,
            year TEXT NOT NULL,
            phone TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
