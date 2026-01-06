# Project Report: AI-Powered Facial Recognition Attendance System

## Abstract
The **AI-Powered Facial Recognition Attendance System** is a modern, contactless solution designed to streamline the attendance recording process in educational institutions and workplaces. Traditional methods like roll calls or biometric fingerprint scanners are time-consuming and often unhygienic. This system leverages computer vision and machine learning (Haar Cascade Classifiers and LBPH Recognizers) to identify individuals in real-time via a camera feed. It automatically logs attendance into a secure database and provides a comprehensive Web Dashboard for administrators to manage students, view real-time statistics, and generate reports. The system ensures high accuracy, prevents proxy attendance, and drastically reduces the time required for attendance tracking.

---

## System Modules

The project is divided into four primary modules:

### 1. Data Collection Module (`photo.py`)
This module is responsible for building the dataset required for training the AI model.
-   **Functionality**: Captures 30 high-speed images of the user's face using the webcam.
-   **Data Entry**: Simultaneously collects user metadata (Name, Class, Year, Phone Number).
-   **Storage**: Saves images to the `images_db` directory and records student details in the SQLite database (`attendance_v2.db`).

### 2. Model Training Module (`Train_Images.py`)
This module processes the raw data to create a lightweight, efficient recognition model.
-   **Algorithm**: Local Binary Patterns Histograms (LBPH).
-   **Process**: Reads images from `images_db`, detects faces, assigns IDs, and trains the `cv2.face.LBPHFaceRecognizer`.
-   **Output**: Generates a `Trainner.yml` file, which is the "brain" of the recognition system.

### 3. Real-Time Recognition Module (`main_code.py`)
The core engine that runs during attendance hours.
-   **Detection**: Uses Haar Cascades to detect faces in the video stream.
-   **Recognition**: Compares detected faces against the trained model (`Trainner.yml`).
-   **Logging**: If a match is found with high confidence, it logs the Name, Date, Time, and Status to the database. It includes logic to prevent duplicate entries for the same session.

### 4. Admin Dashboard Module (`app.py` & Web Interface)
A user-friendly, responsive web interface for system management.
-   **Technology**: Python Flask (Backend), HTML5/CSS3 (Frontend), SQLite (Database).
-   **Features**:
    -   **Live Dashboard**: Shows total students, active classes, and a real-time feed of recent attendance.
    -   **Student Management**: Full CRUD (Create, Read, Update, Delete) capabilities for student records.
    -   **Settings**: Tools to clear logs or factory reset the system.
    -   **Security**: Authenticated login (`admin`/`1234`) to prevent unauthorized access.

---

## System Workflow Description

1.  **Registration**: A new student sits in front of the camera. The administrator runs the Data Collection module, enters the student's details (Name, Class, Year), and the system automatically captures face samples.
2.  **Training**: The administrator runs the Training module once to update the AI model with the new student's face data.
3.  **Deployment**: Two components are started:
    -   The **Web Server** runs in the background, serving the dashboard.
    -   The **Camera System** runs at the entrance or classroom door.
4.  **Attendance**: As students walk past the camera, the system recognizes them instantly. Their "Present" status is logged to the database with a precise timestamp.
5.  **Monitoring**: The administrator views the Web Dashboard to see live updates. If a student's details (e.g., Class or Year) need changing, the admin can edit them directly on the portal. Old data can be cleared regarding semesters via the Settings page.
